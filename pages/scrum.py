import streamlit as st

scrum = st.session_state['selected_session']

back_btn, scrum_title, members_col = st.columns([1,4, 2], vertical_alignment='bottom', gap='small')

scrum_title.header(scrum['name'])
if back_btn.button("Back"):
    st.session_state["selected_session"] = None
    st.switch_page("main.py")

members_col.markdown(f"#### :grey[{len(scrum['members'])} Members]")