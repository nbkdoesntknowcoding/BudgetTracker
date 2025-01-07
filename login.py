import streamlit as st
import yaml
from yaml.loader import SafeLoader
from pathlib import Path

def load_config():
    try:
        config_path = Path(__file__).parent / 'config.yaml'
        with open(config_path, 'r') as file:
            config = yaml.load(file, Loader=SafeLoader)
        return config
    except Exception as e:
        st.error(f"Error loading configuration: {str(e)}")
        return None

def check_password(password, stored_password):
    return password == stored_password

def login_form():
    """Handle login form and authentication"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.session_state.user_name = None
    
    if not st.session_state.authenticated:
        config = load_config()
        if not config:
            st.error("Configuration error. Please contact administrator.")
            return False
        
        col1, col2 = st.columns([3,2])
        
        with col1:
            email = st.text_input("Company Email")
            password = st.text_input("Password", type="password")
            
            if st.button("Login"):
                if email and password:
                    domain = email.split('@')[1] if '@' in email else ''
                    if domain in config['settings']['allowed_domains']:
                        if email in config['credentials']['emails']:
                            stored_password = config['credentials']['emails'][email]['password']
                            if check_password(password, stored_password):
                                st.session_state.authenticated = True
                                st.session_state.user_email = email
                                st.session_state.user_name = config['credentials']['emails'][email]['name']
                                st.rerun()
                            else:
                                st.error("Invalid credentials")
                        else:
                            st.error("Email not registered")
                    else:
                        st.error("Please use your company email")
                else:
                    st.error("Please enter both email and password")
        
        with col2:
            st.markdown("""
            ### Welcome to Acolyte CXO Dashboard
            Please login with your company email to access the dashboard.
            
            For access, please contact:
            - Email: nischaybk@theboringpeople.in
            - Phone: +91-7483511310
            """)
    
    return st.session_state.authenticated

def logout():
    st.session_state.authenticated = False
    st.session_state.user_email = None
    st.session_state.user_name = None
    st.rerun()