import sqlite3
from database import get_db_connection

def update_key():
    key = "AIzaSyBDRDsNr3sBsM6mS_OQpB-b0J2G1m6nPBg"
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('global_api_key', ?)", (key,))
    conn.commit()
    conn.close()
    print("Global API Key Updated.")

if __name__ == "__main__":
    update_key()
