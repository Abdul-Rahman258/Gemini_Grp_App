import hashlib
from firebase_db import create_user_firestore, get_user_by_username

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hash(password) == hashed_text:
        return True
    return False

def create_user(username, password, role='user'):
    return create_user_firestore(username, make_hash(password), role)

def login_user(username, password):
    user = get_user_by_username(username)
    if user and check_hashes(password, user['password_hash']):
        return user
    return None
