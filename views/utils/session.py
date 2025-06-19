import streamlit as st
import json
from pathlib import Path

def initialize_session():
    """Initialize the session state with default values."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'session_data' not in st.session_state:
        st.session_state.session_data = {
            'event_type': None,
            'guest_count': None,
            'budget': None,
            'date': None,
            'location': None,
            'preferences': {}
        }

def clear_session():
    """Clear the current session data."""
    st.session_state.messages = []
    st.session_state.session_data = {
        'event_type': None,
        'guest_count': None,
        'budget': None,
        'date': None,
        'location': None,
        'preferences': {}
    }

def save_session_to_file():
    """Save the current session data to a file."""
    session_file = Path("session_memory.json")
    
    session_data = {
        'messages': st.session_state.messages,
        'session_data': st.session_state.session_data
    }
    
    with open(session_file, 'w') as f:
        json.dump(session_data, f, indent=2)

def load_session_from_file():
    """Load session data from file if it exists."""
    session_file = Path("session_memory.json")
    
    if session_file.exists():
        with open(session_file, 'r') as f:
            data = json.load(f)
            st.session_state.messages = data.get('messages', [])
            st.session_state.session_data = data.get('session_data', {}) 