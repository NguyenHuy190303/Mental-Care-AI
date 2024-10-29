import streamlit as st

def show_sidebar():
    st.sidebar.image("data/images/logo.png", use_column_width=True)
    st.sidebar.markdown('### 🧠 Your AI-powered Mental Health Care Application Based on DSM-5. ')
<<<<<<< HEAD

=======
>>>>>>> feature
    st.sidebar.markdown('Instructions:')
    st.sidebar.markdown('1. 🟢 **Log into your account.**')
    st.sidebar.markdown('2. 💬 **Use the chat feature - "Talk to the AI Psychology Expert" to share your feelings.**')
    st.sidebar.markdown('3. 📈 **Once enough data is collected or you end the conversation, the AI expert will diagnose your mental health status according to DSM-5.**')
    st.sidebar.markdown('4. 📊 **Your mental health status will be saved. You can use the user feature - "Track Your Health Information" to view detailed statistics about your mental health condition.**')
    st.sidebar.markdown('📝 Product by MENTAL CARE team.')
<<<<<<< HEAD
=======

    # Add logout button to the sidebar
    if 'logged_in' in st.session_state and st.session_state.logged_in:
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_info = None
            st.rerun()
>>>>>>> feature
