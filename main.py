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
    st.rerun()


@st.cache_data()
def load_sessions():
    scrum_sessions = (db.collection("scrum")
                      .where( filter=FieldFilter("members", "array_contains", st.session_state["user"]["id"]))
                      .order_by('date', direction='DESCENDING')
                      .get())
    return list(map(ref_to_dict, scrum_sessions))


def check_for_session():
    if st.query_params.get("session_id"):
        session_id = st.query_params["session_id"]
        session = db.collection("scrum").document(session_id).get()
        if session.exists:
            db.collection("scrum").document(session_id).update({
                "members": firestore.ArrayUnion([st.session_state["user"]["id"]]),
                f"member_names.{st.session_state['user']['id']}": st.session_state['user']['name']
            })
            st.session_state["selected_session"] = ref_to_dict(session)
            st.switch_page("pages/scrum.py")


@st.dialog("New Session")
def create_session():
    with st.form("new_session", border=False, enter_to_submit=False):
        session_name = st.text_input("Enter session name")
        if st.form_submit_button("Start session"):
            payload = {
                "name": session_name,
                "creator": st.session_state["user"]["id"],
                "date": firestore.SERVER_TIMESTAMP,
                "members": [st.session_state["user"]["id"]],
                "member_names": {
                    st.session_state["user"]["id"]: st.session_state["user"]["name"]
                }
            }
            time, ref = db.collection("scrum").add(payload)
            payload["id"] = ref.id
            st.cache_data.clear()
            # st.session_state["selected_session"] = payload
            st.rerun()
            # st.switch_page("pages/scrum.py")


if st.session_state.get("user") is None:
    st.title("Scrum Poker 🃏")
    st.text("Login to get started")
    with st.container(border=True):
        name_input = st.text_input("Enter your name")
        email_input = st.text_input("Enter your email")
        if st.button("Submit"):
            login(name_input, email_input)
else:
    col1, col2 = st.columns([5, 1], vertical_alignment='center', gap='large')
    col1.header(f"Welcome to Scrum Poker 🃏, :green[{st.session_state['user']['name']}]")
    if col2.button("Logout", type="tertiary"):
        st.session_state["user"] = None
        st.rerun()
    st.divider()

    check_for_session()

    history_label, new_session_btn = st.columns([3.7,1], vertical_alignment='bottom', gap='large')
    history_label.subheader("Sessions", divider=False)
    if new_session_btn.button("New Session"):
        create_session()

    sessions = load_sessions()
    if not sessions:
        st.write("No scrum sessions found.")
    else:
        event = st.dataframe(
            key="sessions",
            data=sessions,
            on_select="rerun",
            selection_mode="single-row",
            column_order=["name", "date"],
            use_container_width=True,
            column_config={
                'date': st.column_config.DatetimeColumn("Date", format='MMM D Y, H:mm a', timezone='Africa/Nairobi'),
            },
        )

        if event.selection.rows or st.session_state.get("selected_session") is not None:
            selected_session = st.session_state.get("selected_session") or sessions[event.selection.rows[0]]
            if st.button(f"Go to {selected_session['name']}"):
                st.session_state["selected_session"] = selected_session
                st.switch_page("pages/scrum.py")
            st.markdown(f"[Copy this link to share {selected_session['name']}](?session_id={selected_session['id']})")
        else:
            st.write("Select a row from the first column to begin")


