import google.generativeai as genai
from database import get_db_connection

def get_system_api_key():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = 'global_api_key'")
    result = c.fetchone()
    conn.close()
    return result['value'] if result else None

def configure_gemini(api_key):
    genai.configure(api_key=api_key)

def get_gemini_response(prompt, history=[], api_key=None):
    if not api_key:
        return "Error: No API Key provided."
    
    try:
        configure_gemini(api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # Convert internal history format to Gemini history format if needed
        # For now, we'll just send the prompt as a simple request or build a chat session
        chat = model.start_chat(history=history)
        response = chat.send_message(prompt)
        return response.text
    except Exception as e:
        return f"Error calling Gemini API: {str(e)}"
