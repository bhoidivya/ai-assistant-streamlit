# ---------- ENV SETUP ----------
from dotenv import load_dotenv
load_dotenv()

import os
import streamlit as st

# Load API key safely
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    st.error("❌ API key not found. Please check your .env file.")
    st.stop()


# ---------- LANGCHAIN IMPORTS ----------
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_agent


# ---------- TOOLS ----------
@tool
def calculator(a: float, b: float) -> str:
    """Add two numbers and return the result."""
    return f"The sum of {a} and {b} is {a + b}"


@tool
def say_hello(name: str) -> str:
    """Greet a user by name."""
    return f"Hello {name}, I hope you are well today"


# ---------- MODEL ----------
model = ChatOpenAI(
    model="openai/gpt-4o-mini",
    temperature=0.3,
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

tools = [calculator, say_hello]
agent_executor = create_agent(model=model, tools=tools)


# ---------- STREAMLIT UI ----------
st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 AI Assistant")
st.caption("🚀 Powered by LangChain + OpenRouter")

# Sidebar (extra polish)
with st.sidebar:
    st.header("⚙️ Settings")
    st.markdown("**Model:** GPT-4o-mini")
    st.markdown("**Tools:** Calculator, Greeting")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()


# ---------- SESSION MEMORY ----------
if "messages" not in st.session_state:
    st.session_state.messages = []


# ---------- DISPLAY CHAT ----------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ---------- USER INPUT ----------
user_input = st.chat_input("💬 Ask me anything...")

if user_input:
    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate assistant response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

    try:
        for chunk in agent_executor.stream({
            "messages": [HumanMessage(content=user_input)]
        }):
            
            # ✅ HANDLE MODEL OUTPUT
            if "model" in chunk:
                messages = chunk["model"].get("messages", [])
                
                for msg in messages:
                    # Extract actual text from AIMessage
                    if hasattr(msg, "content"):
                        full_response += msg.content
                        response_placeholder.markdown(full_response)

        # fallback
        if not full_response:
            full_response = "⚠️ No response generated."
            response_placeholder.markdown(full_response)

    except Exception as e:
        full_response = f"❌ Error: {str(e)}"
        response_placeholder.markdown(full_response)

    # Save assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response
    })