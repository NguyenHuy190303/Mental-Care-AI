import streamlit as st
import yaml
import hashlib
import os
from src.global_settings import USERS_FILE

# Load data from the YAML file
def load_users():
    if os.path.exists(USERS_FILE) and os.path.getsize(USERS_FILE) > 0:
        with open(USERS_FILE, 'r') as file:
            users = yaml.safe_load(file)
        return users if users else {"usernames": {}}
    else:
        return {"usernames": {}}

# Save data to the YAML file
def save_users(users):
    with open(USERS_FILE, 'w') as file:
        yaml.safe_dump(users, file)

# Hash the password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Verify the password
def verify_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

# Create the registration interface
def register():
    with st.form(key="register"):
        st.subheader('Register')
        username = st.text_input('Username')
        email = st.text_input('Email')
        name = st.text_input('Full name')
        age = st.number_input('Age', min_value=5, max_value=100)
        gender = st.selectbox('Gender', ['Male', 'Female', 'Another'])
        job = st.text_input('Career')
        address = st.text_input('Address')
        password = st.text_input('Password', type='password')
        confirm_password = st.text_input('Confirm Password', type='password')

        if st.form_submit_button('Sign Up'):
            users = load_users()
            if not isinstance(users.get('usernames'), dict):
                users['usernames'] = {}

            if username in users['usernames']:
                st.error('Username is already taken!')
            elif not username or not password:
                st.error('You need to enter a username and password!')
            elif len(users['usernames']) >= 10:
                st.error('The number of users has reached the maximum limit!')
            elif password == confirm_password:
                hashed_password = hash_password(password)
                users['usernames'][username] = {
                    'id': len(users['usernames']) + 1,
                    'name': name,
                    'email': email,
                    'age': age,
                    'gender': gender,
                    'job': job,
                    'address': address,
                    'password': hashed_password
                }
                save_users(users)
                st.session_state.username = username
                st.session_state.logged_in = True
                st.session_state.user_info = f"username: {username}, "
                for key, value in users['usernames'][username].items():
                    if key != 'password':
                        st.session_state.user_info += f"{key}: {value}, "
                st.rerun()
            else:
                st.error('Passwords do not match!')

# Create the login interface
def login():
    with st.form(key="login"):
        st.subheader('Login')
        username = st.text_input('Username')
        password = st.text_input('Password', type='password')

        if st.form_submit_button('Login'):
            users = load_users()
            if not isinstance(users.get('usernames'), dict):
                users['usernames'] = {}

            if username in users['usernames']:
                stored_password = users['usernames'][username]['password']
                if verify_password(stored_password, password):
                    st.session_state.username = username
                    st.session_state.logged_in = True
                    st.session_state.user_info = f"username: {username}, "
                    for key, value in users['usernames'][username].items():
                        if key != 'password':
                            st.session_state.user_info += f"{key}: {value}, "
                    st.rerun()
                else:
                    st.error('Incorrect password!')
            else:
                st.error('Username not found!')

# Guest login interface
def guest_login():
    if st.button('Login as Guest'):
        st.session_state.logged_in = True
        st.session_state.username = 'Guest'
        st.session_state.user_info = f"username: {st.session_state.username}, " + "Information not provided"
        st.rerun()

if __name__ == '__main__':
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        with st.expander('MENTAL CARE AI', expanded=True):
            login_tab, create_tab = st.tabs(
                [
                    "Login",
                    "Sign Up",
                ]
            )
            with create_tab:
                register()
            with login_tab:
                login()
    else:
        st.write(f"Welcome, {st.session_state.username}!")
        # Add logout button in the sidebar
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_info = None
            st.rerun()
