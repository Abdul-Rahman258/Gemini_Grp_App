import firebase_admin
from firebase_admin import credentials
from google.cloud import firestore
from google.oauth2 import service_account
import streamlit as st
import datetime
from google.api_core import exceptions
import json

# Load credentials directly for google-cloud-firestore
# We need to read the project ID from the JSON to be safe, though Client usually infers it.
with open("firebase_key.json", "r") as f:
    key_data = json.load(f)
    project_id = key_data.get("project_id")

cred = service_account.Credentials.from_service_account_file("firebase_key.json")
db = firestore.Client(credentials=cred, project=project_id, database='grpapp')

def get_db():
    return db

def check_db_connection():
    try:
        # Try to access a non-existent document to verify connection/existence
        db.collection('test').document('test').get()
        return True, None
    except exceptions.NotFound as e:
        return False, "Firestore Database not found. Please create it in the Firebase Console."
    except Exception as e:
        return False, str(e)

# --- Users ---
def create_user_firestore(username, password_hash, role='user'):
    users_ref = db.collection('users')
    # Check if username exists
    query = users_ref.where('username', '==', username).limit(1).stream()
    if any(query):
        return False
    
    new_user = {
        'username': username,
        'password_hash': password_hash,
        'role': role,
        'personal_api_key': '',
        'created_at': firestore.SERVER_TIMESTAMP
    }
    users_ref.add(new_user)
    return True

def get_user_by_username(username):
    users_ref = db.collection('users')
    query = users_ref.where('username', '==', username).limit(1).stream()
    for doc in query:
        user_data = doc.to_dict()
        user_data['id'] = doc.id # Add Firestore ID
        return user_data
    return None

def update_user_key(user_id, new_key):
    db.collection('users').document(user_id).update({'personal_api_key': new_key})

def make_user_admin(user_id):
    db.collection('users').document(user_id).update({'role': 'admin'})

def get_all_users():
    users = []
    for doc in db.collection('users').stream():
        u = doc.to_dict()
        u['id'] = doc.id
        users.append(u)
    return users

# --- Chats ---
def create_chat_firestore(user_id, category, title):
    new_chat = {
        'user_id': user_id,
        'category': category,
        'title': title,
        'created_at': firestore.SERVER_TIMESTAMP,
        'participants': []  # Array of user IDs who have access (for private chats)
    }
    _, doc_ref = db.collection('chats').add(new_chat)
    return doc_ref.id

def get_chats_by_category_firestore(user_id, category):
    chats_ref = db.collection('chats')
    
    if category in ['Study', 'Fun']:
        # Shared Categories: Fetch ALL chats in this category
        query = chats_ref.where('category', '==', category)
    else:
        # Private Category: Fetch chats where user is creator OR participant
        # We need to fetch all private chats and filter in Python since Firestore doesn't support OR on different fields easily
        query = chats_ref.where('category', '==', category)
        
    results = []
    for doc in query.stream():
        chat = doc.to_dict()
        chat['id'] = doc.id
        
        # For private chats, only include if user is creator or participant
        if category == 'Private':
            is_creator = chat.get('user_id') == user_id
            is_participant = user_id in chat.get('participants', [])
            if not (is_creator or is_participant):
                continue
        
        results.append(chat)
    
    # Sort in Python to avoid "Index Required" error from Firestore
    # Handle cases where created_at might be None or missing
    def get_sort_key(x):
        val = x.get('created_at')
        if val is None:
            return datetime.datetime.min
        return val

    results.sort(key=get_sort_key, reverse=True)
    return results

def get_chat_details(chat_id):
    doc = db.collection('chats').document(chat_id).get()
    if doc.exists:
        chat = doc.to_dict()
        chat['id'] = doc.id
        return chat
    return None

# --- Messages ---
def save_message_firestore(chat_id, sender_id, sender_name, content, is_ai=False, is_important=False):
    msg_data = {
        'chat_id': chat_id,
        'sender_id': sender_id,
        'sender_name': sender_name,
        'content': content,
        'timestamp': firestore.SERVER_TIMESTAMP,
        'is_ai': is_ai,
        'is_important': is_important
    }
    db.collection('messages').add(msg_data)
    
    # Handle Mentions
    import re
    mentions = re.findall(r'@(\w+)', content)
    for username in mentions:
        # Find user by username
        users_ref = db.collection('users').where('username', '==', username).stream()
        for user_doc in users_ref:
            target_user_id = user_doc.id
            if target_user_id != sender_id: # Don't notify self
                add_unread_mention(target_user_id, chat_id)

def toggle_message_importance(msg_id, current_status):
    db.collection('messages').document(msg_id).update({'is_important': not current_status})

def add_unread_mention(user_id, chat_id):
    user_ref = db.collection('users').document(user_id)
    # Use array_union to add unique chat_id to unread_mentions list
    user_ref.update({'unread_mentions': firestore.ArrayUnion([chat_id])})

def remove_unread_mention(user_id, chat_id):
    user_ref = db.collection('users').document(user_id)
    # Use array_remove to remove chat_id
    user_ref.update({'unread_mentions': firestore.ArrayRemove([chat_id])})

def get_user_unread_mentions(user_id):
    doc = db.collection('users').document(user_id).get()
    if doc.exists:
        return doc.to_dict().get('unread_mentions', [])
    return []

def get_messages_firestore(chat_id):
    msgs_ref = db.collection('messages')
    # Removed order_by to avoid index requirement
    query = msgs_ref.where('chat_id', '==', chat_id)
    
    results = []
    for doc in query.stream():
        msg = doc.to_dict()
        msg['id'] = doc.id
        results.append(msg)
    
    # Sort in Python
    def get_sort_key(x):
        val = x.get('timestamp')
        if val is None:
            return datetime.datetime.min
        return val

    results.sort(key=get_sort_key) # Ascending order
    return results

def get_important_messages(user_id):
    # Fetch all messages marked as important
    # Ideally we should filter by user access, but for now let's fetch all important ones 
    # and filter by chats the user has access to if needed. 
    # For simplicity in this group app, we'll show all important messages from chats the user is part of.
    # Since we don't have easy "user in chat" logic for public chats, we'll just fetch all important messages.
    
    query = db.collection('messages').where('is_important', '==', True)
    results = []
    for doc in query.stream():
        msg = doc.to_dict()
        msg['id'] = doc.id
        results.append(msg)
    return results
def get_system_api_key_firestore():
    doc = db.collection('settings').document('global_api_key').get()
    if doc.exists:
        return doc.to_dict().get('value')
    return None

def set_system_api_key_firestore(key):
    db.collection('settings').document('global_api_key').set({'value': key})

# --- Admin Deletion ---
def delete_user_firestore(user_id):
    db.collection('users').document(user_id).delete()

def delete_chat_firestore(chat_id):
    # Delete messages first
    msgs = db.collection('messages').where('chat_id', '==', chat_id).stream()
    for m in msgs:
        m.reference.delete()
    # Delete chat
    db.collection('chats').document(chat_id).delete()
    
def get_all_chats():
    chats = []
    for doc in db.collection('chats').stream():
        c = doc.to_dict()
        c['id'] = doc.id
        chats.append(c)
    return chats

# --- Participants ---
def add_participant_to_chat(chat_id, user_id):
    chat_ref = db.collection('chats').document(chat_id)
    chat_ref.update({'participants': firestore.ArrayUnion([user_id])})

def remove_participant_from_chat(chat_id, user_id):
    chat_ref = db.collection('chats').document(chat_id)
    chat_ref.update({'participants': firestore.ArrayRemove([user_id])})

def get_chat_participants(chat_id):
    chat = get_chat_details(chat_id)
    if not chat:
        return []
    
    participant_ids = chat.get('participants', [])
    participants = []
    
    for uid in participant_ids:
        user_doc = db.collection('users').document(uid).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            user_data['id'] = user_doc.id
            participants.append(user_data)
    
    return participants
