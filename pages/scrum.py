import streamlit as st
import firebase_admin
from firebase_admin import firestore
from images import waiting
import random
import pandas as pd

db = firestore.client()

scrum = st.session_state['selected_session']
user = st.session_state['user']

back_btn, scrum_title, members_col = st.columns([1, 4, 2], vertical_alignment='bottom', gap='small')

scrum_title.header(scrum['name'])
if back_btn.button("Back"):
    st.session_state["selected_session"] = None
    st.switch_page("main.py")

st.divider()


def submit_vote():
    db.collection("scrum").document(scrum['id']).update({f"votes.{user['id']}": st.session_state['my_vote']})
    st.success('Success! Your vote has been submitted', icon="📤")
    # st.session_state['my_vote'] = None


def member_list():
    st.subheader(f"Members :grey[({len(scrum['members'])})]", divider=True)
    for member_name in scrum['member_names'].values():
        st.write(f":grey[{member_name}]")


def story_form(button_label="Start Story"):
    with st.form("new_story", border=False, enter_to_submit=False):
        story_name = st.text_input("Enter story name", key="story_name")
        if st.form_submit_button(button_label, use_container_width=True):
            db.collection("scrum").document(scrum['id']).update({
                "active_story": story_name,
                "votes": {},
                "voting_closed": False
            })
            st.success(f"Story '{story_name}' has been started. ")
            st.session_state['story_name'] = None
            st.rerun()


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
        if user['id'] in scrum.get('votes', {}):
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
                st.rerun()
        if scrum["creator"] == user["id"]:
            if st.button("Close Voting", use_container_width=True, type="primary"):
                # TODO("send active story data to history")
                db.collection("scrum").document(scrum['id']).update({"voting_closed": True})
                st.success("Voting has been closed. :stopwatch:")
                st.session_state['my_vote'] = None
                st.rerun()
    with members_col:
        member_list()

elif scrum["creator"] == user["id"]:
    waiting_col, story_col = st.columns([2, 1])
    waiting_col.write("Start a story to begin voting. :rocket:  Your team is waiting for you :hourglass_flowing_sand:")
    waiting_col.image(random.choice(waiting))

    with story_col:
        story_form()

else:
    st.write("No active story. ")
    st.write("Voting will begin when scrum master starts a story. ::hourglass_flowing_sand::")
    st.image(random.choice(waiting))
