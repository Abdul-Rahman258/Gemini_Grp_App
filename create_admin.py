import sqlite3
from auth import create_user, make_hash
from database import get_db_connection

def create_admin():
    username = "admin"
    password = "admin123"
    
    # Try to create user first (handles password hashing)
    if create_user(username, password):
        print(f"User '{username}' created.")
    else:
        print(f"User '{username}' already exists.")
        
    # Force update role to admin
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET role = 'admin' WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    print(f"User '{username}' is now an ADMIN.")

if __name__ == "__main__":
    create_admin()
