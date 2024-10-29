import streamlit as st
from src.authenticate import login, register, guest_login
import src.sidebar as sidebar

def main():
    sidebar.show_sidebar()
    
    # Login interface
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        with st.expander('MENTAL CARE AI', expanded=True):
            login_tab, create_tab, guest_tab = st.tabs(
                [
                    "Login",
                    "Create Account",
                    "Guest"
                ]
            )
            with create_tab:
                register()
            with login_tab:
                login()
            with guest_tab:
                guest_login()
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.image("data/images/chat.jpeg")
            if st.button("Talk to the AI Psychology Expert"):
                st.switch_page("pages/2_💬_Chat.py")
        with col2:
            st.image("data/images/chart.jpeg")
            if st.button("Track Your Health Information"):
                st.switch_page("pages/1_📈_user.py")
        st.success(f'Welcome {st.session_state.username}, explore the features of this mental health care app!', icon="🎉")


if __name__ == "__main__":
    main()