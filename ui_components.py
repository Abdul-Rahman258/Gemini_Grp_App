import streamlit as st
from firebase_db import (
    get_chats_by_category_firestore, 
    create_chat_firestore, 
    get_chat_details, 
    get_messages_firestore, 
    save_message_firestore, 
    get_important_messages,
    update_user_key,
    get_system_api_key_firestore,
    set_system_api_key_firestore,
    get_all_users,
    make_user_admin,
    get_db
)
from gemini_utils import get_gemini_response
import datetime

def get_chats_by_category(user_id, category):
    return get_chats_by_category_firestore(user_id, category)

def create_new_chat(user_id, category, title):
    return create_chat_firestore(user_id, category, title)

def render_sidebar():
    st.header("🗂️ Folders")
    
    # Unread Mentions
    from firebase_db import get_user_unread_mentions, remove_unread_mention
    unread_chats = get_user_unread_mentions(st.session_state.user['id'])
    
    categories = ["Private", "Study", "Fun"]
    
    for cat in categories:
        with st.expander(f"📂 {cat}", expanded=False):
            # New Chat Button for this category
            with st.popover(f"➕ New {cat} Chat"):
                new_chat_title = st.text_input(f"Chat Title ({cat})", key=f"new_title_{cat}")
                if st.button(f"Create", key=f"create_{cat}"):
                    if new_chat_title:
                        new_id = create_new_chat(st.session_state.user['id'], cat, new_chat_title)
                        st.session_state.active_chat_id = new_id
                        st.rerun()
            
            # List existing chats
            chats = get_chats_by_category(st.session_state.user['id'], cat)
            for chat in chats:
                # Notification Dot
                label = f"💬 {chat['title']}"
                if chat['id'] in unread_chats:
                    label += " 🔴"
                    
                if st.button(label, key=f"chat_btn_{chat['id']}"):
                    st.session_state.active_chat_id = chat['id']
                    # Clear notification on click
                    if chat['id'] in unread_chats:
                        remove_unread_mention(st.session_state.user['id'], chat['id'])
                    st.rerun()

    if st.session_state.user['role'] == 'admin':
        st.divider()
        if st.button("⚙️ Admin Panel"):
            st.session_state.active_chat_id = "ADMIN"
            st.rerun()

@st.fragment(run_every=3)
def render_messages_area(chat_id):
    # Fetch Messages
    messages = get_messages_firestore(chat_id)
    
    chat_container = st.container(height=500)
    with chat_container:
        if not messages:
            st.info("No messages yet. Start the conversation!")
            
        for msg in messages:
            is_me = msg['sender_id'] == st.session_state.user['id']
            is_ai = msg['is_ai']
            
            # Determine CSS class
            if is_ai:
                msg_class = "ai-message"
                align_style = "align-items: flex-start;"
            elif is_me:
                msg_class = "user-message"
                align_style = "align-items: flex-end;"
            else:
                msg_class = "other-message"
                align_style = "align-items: flex-start;"
                
            # Timestamp formatting
            ts = msg['timestamp']
            if isinstance(ts, datetime.datetime):
                ts_str = ts.strftime("%H:%M")
            else:
                ts_str = ""

            # Custom HTML Rendering
            import re
            content = msg['content']
            # Highlight @mentions (simple regex for @word)
            content = re.sub(r'(@\w+)', r'<span class="mention">\1</span>', content)
            
            col_msg, col_star = st.columns([0.9, 0.1])
            
            with col_msg:
                st.markdown(f"""
                    <div style="display: flex; flex-direction: column; {align_style} width: 100%;">
                        <div class="chat-message {msg_class}">
                            <div class="sender-name">{msg['sender_name']}</div>
                            <div class="message-content">{content}</div>
                            <div class="timestamp">{ts_str}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col_star:
                # Star Button
                star_label = "★" if msg.get('is_important') else "☆"
                if st.button(star_label, key=f"star_{msg['id']}", help="Mark as Important"):
                    from firebase_db import toggle_message_importance
                    toggle_message_importance(msg['id'], msg.get('is_important', False))
                    st.rerun()

        # Auto-Scroll Script
        st.markdown("""
            <script>
            var element = window.parent.document.querySelector('.stContainer');
            if (element) {
                element.scrollTop = element.scrollHeight;
            }
            </script>
        """, unsafe_allow_html=True)

def render_chat_interface(chat_id):
    if chat_id == "ADMIN":
        render_admin_panel()
        return

    # Fetch Chat Details
    chat = get_chat_details(chat_id)
    if not chat:
        st.error("Chat not found.")
        return
    
    st.subheader(f"💬 {chat['title']}")
    
    # Render Messages with Auto-Update
    render_messages_area(chat_id)

    # Chat Input (Outside fragment to avoid focus loss)
    # Gemini Mode Toggle
    gemini_mode = st.toggle("🤖 Ask Gemini", key="gemini_toggle", help="Enable to talk to Gemini without typing @Gemini")
    
    if prompt := st.chat_input("Type your message..."):
        # Save User Message
        save_message_firestore(chat_id, st.session_state.user['id'], st.session_state.user['username'], prompt, is_ai=False)
        
        # Check for @Gemini trigger OR Gemini Mode
        if "@gemini" in prompt.lower() or gemini_mode:
            # Get AI Response
            # Determine API Key (User's personal or System Global)
            api_key = st.session_state.user.get('personal_api_key')
            if not api_key:
                api_key = get_system_api_key_firestore()
                
            if not api_key:
                st.error("No API Key found. Please add one in settings.")
                return

            # Build History for Context (Fetch fresh to include just sent msg)
            messages = get_messages_firestore(chat_id)
            history = []
            for m in messages:
                role = "model" if m['is_ai'] else "user"
                history.append({"role": role, "parts": [m['content']]})
                
            # UI Feedback for AI
            with st.spinner("Thinking..."):
                response_text = get_gemini_response(prompt, history, api_key)
                # Save AI Message
                save_message_firestore(chat_id, 0, "Gemini", response_text, is_ai=True)
                st.rerun()
        else:
            # If not triggering Gemini, just rerun to show the user's message
            st.rerun()

def render_right_panel():
    st.subheader("🔧 Settings & Info")
    
    with st.expander("🔑 API Key Configuration", expanded=True):
        current_key = st.session_state.user.get('personal_api_key') or ""
        new_key = st.text_input("Your Personal Gemini API Key", value=current_key, type="password")
        if st.button("Save Key"):
            update_user_key(st.session_state.user['id'], new_key)
            # Update session state
            st.session_state.user['personal_api_key'] = new_key
            st.success("Key Saved!")
            st.rerun()
            
    st.divider()
    
    # Participants Section (only for Private chats)
    if st.session_state.active_chat_id and st.session_state.active_chat_id != "ADMIN":
        chat = get_chat_details(st.session_state.active_chat_id)
        if chat and chat.get('category') == 'Private':
            st.subheader("👥 Participants")
            
            # Check if current user is the creator
            is_creator = chat.get('user_id') == st.session_state.user['id']
            
            # Show current participants
            from firebase_db import get_chat_participants, add_participant_to_chat, remove_participant_from_chat
            participants = get_chat_participants(st.session_state.active_chat_id)
            
            # Show creator
            db = get_db()
            creator_doc = db.collection('users').document(chat.get('user_id')).get()
            if creator_doc.exists:
                creator = creator_doc.to_dict()
                st.caption(f"👑 Creator: **{creator.get('username')}**")
            
            # Show participants
            if participants:
                st.caption("**Members:**")
                for p in participants:
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"• {p['username']}")
                    if is_creator:
                        if col2.button("🗑️", key=f"remove_participant_{p['id']}", help="Remove"):
                            remove_participant_from_chat(st.session_state.active_chat_id, p['id'])
                            st.rerun()
            
            # Add participant (only creator can do this)
            if is_creator:
                st.caption("**Add Member:**")
                all_users = get_all_users()
                # Filter out users already in chat
                participant_ids = [p['id'] for p in participants]
                available_users = [u for u in all_users if u['id'] not in participant_ids and u['id'] != chat.get('user_id')]
                
                if available_users:
                    user_options = {u['username']: u['id'] for u in available_users}
                    selected_username = st.selectbox("Select user", options=list(user_options.keys()), key="add_participant_select")
                    
                    if st.button("➕ Add to Chat", key="add_participant_btn"):
                        selected_user_id = user_options[selected_username]
                        add_participant_to_chat(st.session_state.active_chat_id, selected_user_id)
                        st.success(f"Added {selected_username}!")
                        st.rerun()
                else:
                    st.caption("No more users to add")
            
            st.divider()
    
    st.subheader("⭐ Important Questions")
    # Fetch important messages for the current user (from all chats they are in)
    # For simplicity, we fetch all important messages and filter if needed, 
    # but here we just show what get_important_messages returns.
    important_msgs = get_important_messages(st.session_state.user['id'])
    
    if important_msgs:
        for msg in important_msgs:
            st.info(f"{msg['sender_name']}: {msg['content'][:50]}...")
        
        # PDF Export
        from fpdf import FPDF
        
        def create_pdf(messages):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Important Questions", ln=1, align='C')
            pdf.ln(10)
            
            for m in messages:
                ts = m['timestamp']
                if isinstance(ts, datetime.datetime):
                    ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    ts_str = str(ts)
                
                # Handle unicode characters roughly (FPDF doesn't support full unicode by default without font setup)
                # We'll replace non-latin characters to avoid errors or use a compatible font if available.
                # For this basic implementation, we'll encode/decode to latin-1 and replace errors.
                content = m['content'].encode('latin-1', 'replace').decode('latin-1')
                sender = m['sender_name'].encode('latin-1', 'replace').decode('latin-1')
                
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(0, 10, txt=f"[{ts_str}] {sender}:", ln=1)
                pdf.set_font("Arial", '', 10)
                pdf.multi_cell(0, 10, txt=content)
                pdf.ln(5)
                
            return pdf.output(dest='S').encode('latin-1')

        pdf_bytes = create_pdf(important_msgs)
        
        st.download_button(
            label="📥 Export PDF",
            data=pdf_bytes,
            file_name="important_questions.pdf",
            mime="application/pdf"
        )
    else:
        st.caption("No important messages marked yet.")
            
    st.divider()
    st.caption("Gemini Group Chat v1.0 (Firebase)")

def render_admin_panel():
    st.title("⚙️ Admin Panel")
    
    st.subheader("Global API Key")
    current_global = get_system_api_key_firestore() or ""
    new_global = st.text_input("System-wide Gemini API Key (Fallback)", value=current_global, type="password")
    if st.button("Update Global Key"):
        set_system_api_key_firestore(new_global)
        st.success("Global Key Updated!")

    st.divider()
    st.subheader("User Management")
    users = get_all_users()
    
    for u in users:
        col1, col2, col3 = st.columns([3, 1, 1])
        col1.write(f"**{u['username']}** ({u['role']})")
        if u['role'] != 'admin':
            if col2.button("Make Admin", key=f"make_admin_{u['id']}"):
                make_user_admin(u['id'])
                st.rerun()
            if col3.button("🗑️ Delete", key=f"del_user_{u['id']}"):
                from firebase_db import delete_user_firestore
                delete_user_firestore(u['id'])
                st.rerun()
                
    st.divider()
    st.subheader("Chat Management")
    from firebase_db import get_all_chats, delete_chat_firestore
    chats = get_all_chats()
    
    for c in chats:
        col1, col2 = st.columns([4, 1])
        col1.write(f"**{c.get('title', 'Untitled')}** ({c.get('category', 'Unknown')})")
        if col2.button("🗑️ Delete", key=f"del_chat_{c['id']}"):
            delete_chat_firestore(c['id'])
            st.rerun()
