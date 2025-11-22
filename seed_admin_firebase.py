from firebase_db import create_user_firestore, make_user_admin, get_user_by_username
import hashlib

def seed_admin():
    username = "admin"
    password = "admin123"
    
    # Check if exists
    user = get_user_by_username(username)
    if user:
        print(f"User '{username}' already exists. Updating role to admin...")
        make_user_admin(user['id'])
    else:
        print(f"Creating user '{username}'...")
        # create_user_firestore hashes the password inside it? 
        # Wait, let's check auth.py. create_user calls create_user_firestore(username, make_hash(password), role)
        # But create_user_firestore takes password_hash directly.
        
        # Let's use the auth.py function to be safe/consistent if possible, 
        # but auth.py imports firebase_db, so importing auth here might be circular if not careful.
        # Let's just do it manually with the hash function.
        
        password_hash = hashlib.sha256(str.encode(password)).hexdigest()
        create_user_firestore(username, password_hash, role='admin')
        
    print(f"✅ Admin user ready.\nUsername: {username}\nPassword: {password}")

if __name__ == "__main__":
    seed_admin()
