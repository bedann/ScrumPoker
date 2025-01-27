import streamlit as st
from firebase_admin import firestore
from images import waiting
import random
import pandas as pd
import time
from queue import Queue
from utils import ref_to_dict
from statistics import mode

db = firestore.client()
q = Queue(maxsize=3)

scrum = st.session_state['selected_session']
user = st.session_state['user']

st.set_page_config(
    page_title=f"Scrum | {scrum['name']}" if scrum else "Scrum Poker 🃏︎",
    layout='centered',
)
# doc_watch = None


def on_snapshot(doc_snapshot, changes, read_time):
    for doc in doc_snapshot:
        print(f'Received document snapshot: {doc.id}')
        q.put(ref_to_dict(doc))


def listen_to_changes():
    # global doc_watch
    if st.session_state.get("listener") is None:
        st.session_state["listener"] = True
        doc_ref = db.collection("scrum").document(scrum['id'])
        doc_watch = doc_ref.on_snapshot(on_snapshot)

    while True:
        # time.sleep(1)
        doc = q.get()
        print("Updating session...")
        st.session_state['selected_session'] = doc
        if doc == scrum:
            continue
        else:
            break
    st.session_state["listener"] = None
    st.rerun()  # this is the problem, we need a way to rerun the script


back_btn, scrum_title, members_col = st.columns([1, 4, 2], vertical_alignment='bottom', gap='small')

scrum_title.header(scrum['name'])
if back_btn.button("Back"):
    st.session_state["selected_session"] = None
    st.session_state["listener"] = None
    # if doc_watch:
    #     doc_watch.unsubscribe()
    st.switch_page("main.py")


def load_history():
    history = db.collection("scrum").document(scrum['id']).collection("history").order_by("date",
                                                                                          direction="DESCENDING").get()
    return list(map(ref_to_dict, history))


def submit_vote():
    db.collection("scrum").document(scrum['id']).update({f"votes.{user['id']}": st.session_state['my_vote']})
    st.success('Success! Your vote has been submitted', icon="📤")
    st.session_state['my_vote'] = None
    st.session_state['listener'] = None


def member_list():
    st.subheader(f"Members :grey[({len(scrum['members'])})]", divider=True)
    for member_id in scrum['members']:
        voted = member_id in scrum.get('votes', {}).keys()
        name = scrum['member_names'][member_id] or 'Unknown'
        st.write(f":{'green' if voted else 'grey'}[{name}]")


def create_form():
    st.session_state.new_story = st.session_state.story_name
    st.session_state.story_name = ''
    story_data = {
        "active_story": st.session_state.new_story,
        "votes": {},
        "voting_closed": False
    }
    db.collection("scrum").document(scrum['id']).update(story_data)
    st.session_state['listener'] = None


def story_form(button_label="Start Story"):
    if 'new_story' not in st.session_state:
        st.session_state.new_story = ''
    with st.form("new_story_form", border=False, enter_to_submit=False):
        st.text_input("Enter story name", key="story_name")
        st.form_submit_button(button_label, use_container_width=True, on_click=create_form)


def close_vote():
    result = 0
    count = 0
    if scrum.get('votes'):
        result = mode(scrum['votes'].values())
        count = len(scrum['votes'])
    db.collection("scrum").document(scrum['id']).collection("history").add({
        "story": scrum['active_story'],
        "votes": count,
        "result": result,
        "date": firestore.SERVER_TIMESTAMP
    })
    st.success("Voting has been closed. :stopwatch:")
    st.session_state['my_vote'] = None
    st.session_state['listener'] = None
    db.collection("scrum").document(scrum['id']).update({"voting_closed": True})


story_tab, history_tab = st.tabs(["Voting", "History"])

with story_tab:
    if scrum.get("active_story") and scrum.get('voting_closed', False):
        st.write(scrum.get("active_story"))
        st.write(f"Results are in! :tada: :green[Total Votes: {len(scrum.get('votes', {}).values())}]")

        results_col, members_votes_col = st.columns([2, 1], border=True)
        with results_col:
            series = pd.Series(scrum.get('votes', {}), dtype=int)
            distribution = series.value_counts()

            st.bar_chart(
                data=distribution,
                use_container_width=True,
                height=300,
                color=["#FF5733"]
            )
        with members_votes_col:
            if user['id'] == scrum['creator']:
                story_form(button_label="Start Another Story")

            member_votes = map(lambda x: (scrum['member_names'][x[0]], x[1]), scrum.get('votes', {}).items())
            df = pd.DataFrame(member_votes, columns=["Member", "Vote"])
            st.table(df)

    elif scrum.get("active_story"):
        st.subheader(f":medal: :green[{scrum['active_story']}]")
        vote_col, members_col = st.columns([2, 1], border=True)

        with vote_col:
            options1 = ["1", "2", "3", "5"]
            options2 = ["8", "13", "21"]
            normal_col, complex_col = st.columns(2)

            vote = st.session_state.get("my_vote")

            with normal_col:
                for option in options1:
                    if st.button(option, use_container_width=True, key=option,
                                 type=("primary" if vote == option else "secondary")):
                        st.session_state['my_vote'] = option
                        st.rerun()

            with complex_col:
                for option in options2:
                    if st.button(option, use_container_width=True, key=option,
                                 type=("primary" if vote == option else "secondary")):
                        st.session_state['my_vote'] = option
                        st.rerun()

            if vote:
                st.write("You can change your vote until Scrum Master closes the vote. :timer_clock:")
                if st.button("SUBMIT VOTE", use_container_width=True,
                             type="primary" if scrum["creator"] != user["id"] else "secondary"):
                    submit_vote()
            if scrum["creator"] == user["id"]:
                if st.button("Close Voting", use_container_width=True, type="primary"):
                    close_vote()
        with members_col:
            member_list()

    elif scrum["creator"] == user["id"]:
        waiting_col, story_col = st.columns([2, 1])
        waiting_col.write(
            "Start a story to begin voting. :rocket:  Your team is waiting for you :hourglass_flowing_sand:")
        waiting_col.image(random.choice(waiting))

        with story_col:
            story_form()
            member_list()

    else:
        waiting_col, member_col = st.columns([2, 1])
        waiting_col.write("No active story. ")
        waiting_col.write("Voting will begin when scrum master starts a story. :hourglass_flowing_sand:")
        waiting_col.image(random.choice(waiting))
        with member_col:
            member_list()

with history_tab:
    history = load_history()
    if not history:
        st.write("No stories found.")
    else:
        st.dataframe(history, use_container_width=True, column_order=["story", "result", "votes", "date"])

if st.session_state.get("listener") is None:
    print("Listening to changes...")
    listen_to_changes()
    print("Listening to changes STOPPED >>>>...")
