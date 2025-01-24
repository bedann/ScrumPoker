import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import firestore
from utils import *
from google.cloud.firestore_v1 import FieldFilter

fb_credentials = st.secrets["firebase"]['settings']
cred = firebase_admin.credentials.Certificate(dict(fb_credentials))

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

st.set_page_config(
    page_title="Scrum Poker 🃏︎",
    layout='centered',
)


def login(username, email):
    user = db.collection("users").where(filter=FieldFilter("email", "==", email)).get()
    if not user:
        db.collection("users").add({"name": username, "email": email})
        user = db.collection("users").where(filter=FieldFilter("email", "==", email)).get()
    user = ref_to_dict(user[0])
    st.session_state["user"] = user
    write_settings("email", email)
    st.rerun()


@st.cache_data
def load_sessions():
    scrum_sessions = (db.collection("scrum")
                      .where("members", "array_contains", st.session_state["user"]["id"])
                      .order_by('date', direction='DESCENDING')
                      .get())
    return list(map(ref_to_dict, scrum_sessions))


@st.dialog("New Session")
def create_session():
    with st.form("new_session", border=False, enter_to_submit=False):
        session_name = st.text_input("Enter session name")
        submit_button = st.form_submit_button("Start session")


if st.session_state.get("user") is None:
    cached_user_email = read_settings('email')
    if cached_user_email:
        user = db.collection("users").where(filter=FieldFilter("email", "==", cached_user_email)).get()
        if user:
            st.session_state["user"] = ref_to_dict(user[0])

    name_input = st.text_input("Enter your name")
    email_input = st.text_input("Enter your email")
    if st.button("Submit"):
        login(name_input, email_input)
else:
    st.header(f"Welcome to Scrum Poker 🃏, :green[{st.session_state['user']['name']}]")
    st.divider()

    history_label, new_session_btn = st.columns([2, 1], vertical_alignment='bottom')
    history_label.subheader("History", divider=False)
    if new_session_btn.button("New Session"):
        create_session()

    sessions = load_sessions()
    if not sessions:
        st.write("No scrum sessions found.")
    else:
        st.table(sessions)



