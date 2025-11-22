import google.generativeai as genai
from database import get_db_connection

def get_any_api_key():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Try global key
    c.execute("SELECT value FROM settings WHERE key = 'global_api_key'")
    result = c.fetchone()
    if result and result['value']:
        return result['value']
        
    # Try to find any user key
    c.execute("SELECT personal_api_key FROM users WHERE personal_api_key IS NOT NULL AND personal_api_key != ''")
    result = c.fetchone()
    if result and result['personal_api_key']:
        return result['personal_api_key']
        
    return None

def list_models():
    api_key = "AIzaSyBDRDsNr3sBsM6mS_OQpB-b0J2G1m6nPBg"
    if not api_key:
        print("No API Key found in database to test with.")
        return

    print(f"Using API Key: {api_key[:5]}...{api_key[-5:]}")
    genai.configure(api_key=api_key)
    
    try:
        print("Listing available models...")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models()
