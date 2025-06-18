import streamlit as st
from views.components.sidebar import show_sidebar
from views.components.chat import show_chat_interface
from views.utils.session import initialize_session, clear_session

def show_planner_page():
    # Initialize session if not already done
    if 'messages' not in st.session_state:
        initialize_session()
    
    # Sidebar
    with st.sidebar:
        show_sidebar()
    
    # Main content area
    st.title("Event Planning Assistant")
    
    # Chat interface
    show_chat_interface()
    
    # Input area
    user_input = st.text_area(
        "Type your message here...",
        height=100,
        max_chars=1000,
        key="user_input"
    )
    
    # Send button
    if st.button("Send", use_container_width=True):
        if user_input:
            # Add user message to chat
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # TODO: Process with LLM
            # Placeholder for LLM processing
            response = "This is a placeholder response. LLM integration pending."
            
            # Add assistant response to chat
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Clear input
            st.session_state.user_input = ""
            st.rerun() 