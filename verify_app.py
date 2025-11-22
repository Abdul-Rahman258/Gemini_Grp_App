from database import init_db, get_db_connection
from auth import create_user, login_user
import os

def test_app_logic():
    print("Testing Database and Auth Logic...")
    
    # 1. Init DB
    if os.path.exists("chat_app.db"):
        os.remove("chat_app.db")
    init_db()
    print("✅ Database Initialized")

    # 2. Create User
    assert create_user("testuser", "password123") == True
    print("✅ User Created")
    
    # 3. Duplicate User Check
    assert create_user("testuser", "password123") == False
    print("✅ Duplicate User Prevented")

    # 4. Login
    user = login_user("testuser", "password123")
    assert user is not None
    assert user['username'] == "testuser"
    print("✅ Login Successful")

    # 5. Failed Login
    assert login_user("testuser", "wrongpass") is None
    print("✅ Invalid Login Handled")

    # 6. Create Chat
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO chats (user_id, category, title) VALUES (?, ?, ?)", (user['id'], 'Study', 'Math Help'))
    chat_id = c.lastrowid
    conn.commit()
    print(f"✅ Chat Created (ID: {chat_id})")

    # 7. Save Message
    c.execute("INSERT INTO messages (chat_id, sender_id, sender_name, content) VALUES (?, ?, ?, ?)", 
              (chat_id, user['id'], user['username'], "Hello World"))
    conn.commit()
    print("✅ Message Saved")

    # 8. Verify Message
    msg = c.execute("SELECT * FROM messages WHERE chat_id = ?", (chat_id,)).fetchone()
    assert msg['content'] == "Hello World"
    print("✅ Message Retrieved")
    
    conn.close()
    print("\nALL TESTS PASSED!")

if __name__ == "__main__":
    test_app_logic()
