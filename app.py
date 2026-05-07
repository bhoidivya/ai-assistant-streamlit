# ---------- ENV SETUP ----------
from dotenv import load_dotenv
load_dotenv()

import os
import streamlit as st

# Load API key
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    st.error("❌ API key not found. Please check your .env file.")
    st.stop()

# ---------- LANGCHAIN IMPORTS ----------
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_agent
from datetime import datetime


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
    """Returns current date and time"""
    return str(datetime.now())


# ---------- MODEL ----------
model = ChatOpenAI(
    model="openai/gpt-4o-mini",
    temperature=0.3,
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

tools = [calculator, say_hello, current_time]
agent_executor = create_agent(model=model, tools=tools)


# ---------- STREAMLIT UI ----------
st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 AI Assistant")
st.caption("🚀 Powered by LangChain + OpenRouter")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    st.markdown("**Model:** GPT-4o-mini")
    st.markdown("**Tools:** Calculator, Greeting, Time")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.history = []
        st.rerun()


# ---------- SESSION MEMORY ----------
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
    # Save user message (UI)
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # Save user message (memory for AI)
    st.session_state.history.append(HumanMessage(content=user_input))

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()

        try:
            response = agent_executor.invoke({
                "messages": st.session_state.history
            })

            assistant_msg = response["messages"][-1]

            # Extract text safely
            if hasattr(assistant_msg, "content"):
                full_response = assistant_msg.content
            else:
                full_response = str(assistant_msg)

            response_placeholder.markdown(full_response)

            # Save assistant response (memory + UI)
            st.session_state.history.append(assistant_msg)

        except Exception as e:
            full_response = f"❌ Error: {str(e)}"
            response_placeholder.markdown(full_response)

    # Save assistant message (UI)
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response
    })