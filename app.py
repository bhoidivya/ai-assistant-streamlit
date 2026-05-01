import streamlit as st
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import os

# Load env variables
load_dotenv()

# ---------- Tools ----------
@tool
def calculator(a: float, b: float) -> str:
    """Add two numbers and return the result."""
    return f"The sum of {a} and {b} is {a + b}"


@tool
def say_hello(name: str) -> str:
    """Greet a user by name."""
    return f"Hello {name}, I hope you are well today"

# ---------- Model ----------
model = ChatOpenAI(
    model="openai/gpt-4o-mini",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

tools = [calculator, say_hello]
agent_executor = create_react_agent(model, tools)

# ---------- UI ----------
st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="centered")

st.title("🤖 AI Assistant")
st.caption("Powered by LangChain + OpenRouter")

# Session memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_input = st.chat_input("Ask me anything...")

if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        for chunk in agent_executor.stream({
            "messages": [HumanMessage(content=user_input)]
        }):
            if "agent" in chunk:
                for msg in chunk["agent"]["messages"]:
                    full_response += msg.content
                    response_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})