# ---------- ENV SETUP ----------
from dotenv import load_dotenv
load_dotenv()

import os
import sqlite3
import bcrypt
import streamlit as st
from datetime import datetime
import pytz

# ---------- API KEY ----------
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    st.error("❌ API key not found")
    st.stop()

# ---------- LANGCHAIN IMPORTS ----------
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_agent

# ---------- DATABASE ----------
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
''')

conn.commit()

# ---------- AUTH FUNCTIONS ----------
def create_user(username, password):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    try:
        c.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed)
        )
        conn.commit()
        return True
    except:
        return False


def login_user(username, password):
    c.execute(
        "SELECT password FROM users WHERE username = ?",
        (username,)
    )

    result = c.fetchone()

    if result:
        stored_password = result[0]

        if bcrypt.checkpw(password.encode(), stored_password):
            return True

    return False

# ---------- TOOLS ----------
@tool

def calculator(a: float, b: float) -> str:
    """Add two numbers and return the result."""
    return f"The sum of {a} and {b} is {a + b}"


@tool

def say_hello(name: str) -> str:
    """Greet a user by name."""
    return f"Hello {name}, I hope you are well today"


@tool

def current_time() -> str:
    """Returns current IST time"""
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist).strftime("%I:%M %p, %d %B %Y")

# ---------- MODEL ----------
model = ChatOpenAI(
    model="openai/gpt-4o-mini",
    temperature=0.3,
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

tools = [calculator, say_hello, current_time]
agent_executor = create_agent(model=model, tools=tools)

# ---------- STREAMLIT CONFIG ----------
st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="centered"
)

# ---------- SESSION ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""
    
# ---------- LOGIN / SIGNUP PAGE ----------
if not st.session_state.logged_in:

    st.title("🔐 AI Assistant")

    st.markdown("""
    Welcome to the AI Assistant 🤖

    - New user? → Create an account in **Sign Up**
    - Existing user? → Use **Login**
    """)

    tab1, tab2 = st.tabs(["🔑 Login", "🆕 Sign Up"])

    # ---------- LOGIN TAB ----------
    with tab1:

        st.subheader("Login")

        login_username = st.text_input(
            "Username",
            key="login_user"
        )

        login_password = st.text_input(
            "Password",
            type="password",
            key="login_pass"
        )

        if st.button("Login"):

            if login_user(login_username, login_password):

                st.session_state.logged_in = True
                st.session_state.username = login_username

                st.success("✅ Login successful")
                st.rerun()

            else:
                st.error("❌ Invalid username or password")

    # ---------- SIGNUP TAB ----------
    with tab2:

        st.subheader("Create Account")

        signup_username = st.text_input(
            "Choose Username",
            key="signup_user"
        )

        signup_password = st.text_input(
            "Choose Password",
            type="password",
            key="signup_pass"
        )

        if st.button("Create Account"):

            if create_user(signup_username, signup_password):

                st.success("✅ Account created successfully")
                st.info("👉 Now go to Login tab")

            else:
                st.error("❌ Username already exists")
                
# ---------- MAIN APP ----------
else:

    st.title("🤖 AI Assistant")

    st.success(f"✅ Logged in as: {st.session_state.username}")

# ---------- SIDEBAR ----------
    with st.sidebar:

        st.header("⚙️ Settings")

        st.markdown(
            f"**User:** {st.session_state.username}"
        )

        st.markdown("**Model:** GPT-4o-mini")

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
            
             # ---------- CHAT MEMORY ----------
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "history" not in st.session_state:
        st.session_state.history = []

    # ---------- DISPLAY CHAT ----------
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ---------- USER INPUT ----------
    user_input = st.chat_input("💬 Ask me anything...")

    if user_input:

        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        st.session_state.history.append(
            HumanMessage(content=user_input)
        )

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):

            response_placeholder = st.empty()

            try:

                response = agent_executor.invoke({
                    "messages": st.session_state.history
                })

                assistant_msg = response["messages"][-1]

                if hasattr(assistant_msg, "content"):
                    full_response = assistant_msg.content
                else:
                    full_response = str(assistant_msg)

                response_placeholder.markdown(full_response)

                st.session_state.history.append(assistant_msg)

            except Exception as e:
                full_response = f"❌ Error: {str(e)}"
                response_placeholder.markdown(full_response)

        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response
        })