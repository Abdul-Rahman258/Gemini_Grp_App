import streamlit as st
# from database import init_db, get_db_connection # Removed for Firebase
from auth import login_user, create_user
import ui_components as ui
from firebase_db import check_db_connection

# Initialize Database
# init_db() # No longer needed for Firebase

st.set_page_config(page_title="Gemini Group Chat", layout="wide")

# Check Firebase Connection
db_connected, db_error = check_db_connection()
if not db_connected:
    st.error(f"❌ Database Error: {db_error}")
    st.info("👉 **Action Required**: Go to the [Firebase Console](https://console.firebase.google.com/), select your project, and create a **Firestore Database** (in Native mode).")
    st.stop()

# Session State Initialization
if 'user' not in st.session_state:
    st.session_state.user = None
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'login' # login, chat, admin
if 'active_chat_id' not in st.session_state:
    st.session_state.active_chat_id = None

def main():
    # Custom CSS for premium feel
    st.markdown("""
        <style>
        /* Main Background */
        .stApp {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            font-family: 'Inter', sans-serif;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #111827;
            border-right: 1px solid #374151;
        }
        
        /* Chat Message Bubbles */
        .chat-message {
            padding: 1rem;
            border-radius: 1rem;
            margin-bottom: 1rem; 
            display: flex;
            flex-direction: column;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }
        
        .user-message {
            background: rgba(59, 130, 246, 0.2); /* Blue tint */
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-bottom-right-radius: 0.2rem;
            margin-left: 2rem;
        }
        
        .other-message {
            background: rgba(75, 85, 99, 0.4); /* Gray tint */
            border: 1px solid rgba(75, 85, 99, 0.3);
            border-bottom-left-radius: 0.2rem;
            margin-right: 2rem;
        }
        
        .ai-message {
            background: rgba(16, 185, 129, 0.15); /* Green tint */
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-bottom-left-radius: 0.2rem;
            margin-right: 2rem;
        }
        
        /* Text Styling */
        .sender-name {
            font-size: 0.75rem;
            font-weight: 600;
            margin-bottom: 0.25rem;
            color: #9ca3af;
        }
        
        .message-content {
            font-size: 0.95rem;
            line-height: 1.5;
            color: #f3f4f6;
        }
        
        .timestamp {
            font-size: 0.7rem;
            color: #6b7280;
            align_self: flex-end;
            margin-top: 0.25rem;
        }
        
        /* Input Area */
        .stChatInputContainer {
            padding-bottom: 1rem;
        }
        
        /* Buttons */
        .stButton button {
            background-color: #3b82f6;
            color: white;
            border-radius: 0.5rem;
            border: none;
            transition: all 0.2s;
        }
        .stButton button:hover {
            background-color: #2563eb;
            transform: translateY(-1px);
        }
        
        /* Mentions */
        .mention {
            color: #fbbf24; /* Amber-400 */
            font-weight: 700;
            background: rgba(251, 191, 36, 0.1);
            padding: 0 4px;
            border-radius: 4px;
        }
        </style>
    """, unsafe_allow_html=True)

    if st.session_state.user is None:
        render_login()
    else:
        render_main_app()

def render_login():
    st.title("Gemini Group Chat 🤖")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                user = login_user(username, password)
                if user:
                    st.session_state.user = user
                    st.session_state.current_view = 'chat'
                    st.rerun()
                else:
                    st.error("Invalid username or password")

    with tab2:
        with st.form("register_form"):
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            submit_reg = st.form_submit_button("Register")
            
            if submit_reg:
                if create_user(new_user, new_pass):
                    st.success("Account created! Please login.")
                else:
                    st.error("Username already exists.")

def render_main_app():
    # Sidebar for Navigation
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.user['username']}")
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()
        
        st.divider()
        ui.render_sidebar()

    # Main Layout: Chat Area (Left/Center) + Info Panel (Right)
    col_chat, col_info = st.columns([3, 1])

    with col_chat:
        if st.session_state.active_chat_id:
            ui.render_chat_interface(st.session_state.active_chat_id)
        else:
            st.info("Select or create a chat from the sidebar to start.")

    with col_info:
        ui.render_right_panel()

if __name__ == "__main__":
    main()
