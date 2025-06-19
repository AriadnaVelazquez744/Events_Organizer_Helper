import streamlit as st
from views.components.sidebar import show_sidebar
from views.components.chat import show_chat_interface
from views.utils.session import initialize_session, clear_session

def show_planner_page():
    # Initialize session if not already done
    if 'messages' not in st.session_state:
        initialize_session()
    
    if 'current_query' not in st.session_state:
        st.session_state.current_query = ""
    
    # Custom CSS for modern chat interface
    st.markdown("""
        <style>
            .main {
                padding: 0;
                margin: 0;
            }
            .stTextArea textarea {
                border-radius: 20px;
                padding: 15px;
                font-size: 16px;
                border: 1px solid #e0e0e0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .stTextArea textarea:focus {
                border-color: #4CAF50;
                box-shadow: 0 2px 8px rgba(76,175,80,0.2);
            }
            .stButton button {
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 16px;
                background-color: #4CAF50;
                color: white;
                border: none;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .stButton button:hover {
                background-color: #45a049;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            }
            .chat-container {
                padding: 20px;
                height: calc(100vh - 200px);
                overflow-y: auto;
            }
            .input-container {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                padding: 20px;
                background-color: white;
                border-top: 1px solid #e0e0e0;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        show_sidebar()
    
    # Main content area
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    show_chat_interface()
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Input area in a fixed position at the bottom
    st.markdown("<div class='input-container'>", unsafe_allow_html=True)
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_area(
            "Type your message here...",
            value=st.session_state.current_query,
            height=100,
            max_chars=1000,
            key="user_input",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
        if st.button("Send", use_container_width=True):
            if user_input:
                # Add user message to chat
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                # TODO: Process with LLM
                # Placeholder for LLM processing
                response = "This is a placeholder response. LLM integration pending."
                
                # Add assistant response to chat
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Clear input and current query
                st.session_state.user_input = ""
                st.session_state.current_query = ""
                st.rerun() 