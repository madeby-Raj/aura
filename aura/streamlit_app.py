# streamlit_app.py
import streamlit as st
from nlp_engine import get_response
from db import init_db, log_chat  # optional; if you added db.py earlier

st.set_page_config(page_title="AURA — AI Companion", layout="centered")

# Initialize DB (safe: will create DB if exists)
try:
    init_db()
except Exception:
    pass

st.title("AURA — All-Rounder AI Companion")
st.write("Text demo: chat below. (Local app supports voice; cloud version is text-only.)")

if "history" not in st.session_state:
    st.session_state.history = []  # list of (role, text)

def send_message(user_text: str):
    user_text = user_text.strip()
    if not user_text:
        return
    # log user
    st.session_state.history.append(("user", user_text))
    try:
        log_chat("user", user_text)
    except Exception:
        pass

    # get response (text-only)
    try:
        resp = get_response(user_text)
    except Exception as e:
        resp = "AURA encountered an error handling that input."
        # optionally show error for debugging (comment out if undesired)
        # resp += f" ({e})"

    st.session_state.history.append(("aura", resp))
    try:
        log_chat("aura", resp)
    except Exception:
        pass

# Input area
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("You", placeholder="Ask something (e.g. 'Who is Ada Lovelace?', 'Remind me in 1 min to stretch')", key="user_input")
    submitted = st.form_submit_button("Send")
    if submitted and user_input:
        send_message(user_input)

# Show chat (most recent last)
st.markdown("---")
for role, text in st.session_state.history[-30:]:
    if role == "user":
        st.markdown(f"**You:** {text}")
    else:
        st.markdown(f"**AURA:** {text}")

# quick example buttons
st.markdown("---")
st.markdown("**Quick examples:**")
col1, col2, col3 = st.columns(3)
if col1.button("Who is Elon Musk?"):
    send_message("Who is Elon Musk?")
if col2.button("Play song Believer"):
    send_message("Play song Believer")
if col3.button("Remind me in 10 seconds to stretch"):
    send_message("Remind me in 10 seconds to stretch")

st.markdown(
    "-----\n"
    "Note: This deployed Streamlit app is text-only. For microphone/voice demos run `python main.py` locally."
)
