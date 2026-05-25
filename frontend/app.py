"""
Streamlit frontend for Text-to-SQL Chatbot.
Provides a chat interface that communicates with the FastAPI backend.
"""
import streamlit as st
import httpx
import pandas as pd

# FastAPI backend URL
API_URL = "http://localhost:8000"

st.set_page_config(page_title="DB Chatbot", page_icon="🤖")
st.title("🤖 Ask Your Database")
st.markdown("Ask any question in plain English — no SQL needed!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_sql" not in st.session_state:
    st.session_state.last_sql = None

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if user_input := st.chat_input("e.g. What is the price of product ID 1?"):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Call FastAPI backend
                response = httpx.post(
                    f"{API_URL}/api/v1/query",
                    json={
                        "question": user_input,
                        "last_sql": st.session_state.last_sql
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()

                # Handle clarification needed
                if result.get("clarification_needed"):
                    reply = f"❓ {result['clarification_needed']}"
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                else:
                    # Display data table if available
                    if result.get("data") and result["data"].get("rows"):
                        df = pd.DataFrame(
                            result["data"]["rows"],
                            columns=result["data"]["columns"]
                        )
                        st.dataframe(df)

                    # Show SQL query in expander
                    if result.get("sql_query"):
                        with st.expander("🔍 View generated SQL"):
                            st.code(result["sql_query"], language="sql")
                        st.session_state.last_sql = result["sql_query"]

                    # Display natural language answer
                    reply = result.get("answer", "No response received.")
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})

            except httpx.RequestError as e:
                reply = f"❌ Error connecting to backend: {str(e)}"
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                reply = f"❌ Unexpected error: {str(e)}"
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
