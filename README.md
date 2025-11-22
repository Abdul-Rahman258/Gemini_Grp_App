# Gemini Group Chat App

A Streamlit-based group chat application powered by Google's Gemini API.

## Features
- **Multi-user Support**: Login and Registration system.
- **Group Chat**: Create chats in different categories (Private, Study, Fun).
- **Gemini Integration**: Chat with AI using your personal API key or a system-wide key.
- **Admin Panel**: Manage users and set a global fallback API key.
- **Important Questions**: Mark messages as important and export them.

## How to Run Locally

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the App**:
   ```bash
   streamlit run app.py
   ```

3. **Login**:
   - Register a new account on the login screen.
   - The first user does not automatically become admin (you can change this in the database or use the provided `verify_app.py` logic to seed an admin if needed, or just use the app to register).

## Deploying to Streamlit Cloud (Free)

1. **Push to GitHub**:
   - Create a new repository on GitHub.
   - Push all these files to the repository.

2. **Deploy**:
   - Go to [share.streamlit.io](https://share.streamlit.io/).
   - Connect your GitHub account.
   - Select your new repository and the `app.py` file.
   - Click **Deploy**.

> [!WARNING]
> **Data Persistence on Streamlit Cloud**:
> Streamlit Cloud's free tier does not persist local files (like `chat_app.db`) after the app restarts or goes to sleep. This means **all users and chats will be lost** if the app reboots.
> For a permanent solution, you would need to connect this to a cloud database (like Google Firestore or AWS RDS), which requires more advanced setup.
