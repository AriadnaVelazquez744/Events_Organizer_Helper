"""
Chat page for the Events Organizer Helper.
Provides an interactive chat interface with OpenRouter API.
"""

import streamlit as st
import json
from typing import List
#from api.openrouter_client import SyncOpenRouterClient, ChatMessage
from config import get_config
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from main import initialize_system, Comunication
import src.agents.session_memory as sm


#from interface.api.openrouter_client import SyncOpenRouterClient
from interface.api.fireworks_client import SyncFireworksClient, ChatMessage
from interface.utils.llm_helpers import process_user_input
from interface.utils.session_helpers import instance_missing_fields

# Instantiate the LLM client using config (no need to pass config explicitly)
#llm_client = SyncOpenRouterClient()
llm_client = SyncFireworksClient()

def chat_page():
    """Main chat page function."""
    
    st.title("💬 Chat with Event Planner System")
    st.markdown("Ask me anything about event planning and organization!")
    

    # Set all sessions to inactive before any system initialization
    if "memory_manager" in st.session_state:
        st.session_state.memory_manager.set_all_sessions_inactive()
    else:
        # If not yet in session_state, create a temporary one to perform the action
        temp_memory_manager = sm.SessionMemoryManager()
        temp_memory_manager.set_all_sessions_inactive()

    # Initialize backend system if not already done
    if "system" not in st.session_state:
        st.session_state.system = initialize_system()
        st.session_state.planner = st.session_state.system["planner"]
        st.session_state.memory_manager = st.session_state.system["memory"]

    # User ID management
    if "user_id" not in st.session_state or st.session_state.user_id is None:
        st.session_state.user_id = st.session_state.memory_manager.generate_unique_user_id()

    # Session ID management
    if "session_id" not in st.session_state or st.session_state.session_id is None:
        st.session_state.session_id = st.session_state.planner.create_session(st.session_state.user_id)

    # Chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "response_planner" not in st.session_state:
        st.session_state.response_planner = None
        
    instance_missing_fields()

    # Sidebar for session/user controls
    with st.sidebar:
        st.header("Session Controls")
        # Archive current session before creating a new one
        if st.button("🆕 New Session"):
            # Archive the current session if it exists
            if "session_id" in st.session_state and st.session_state.session_id is not None:
                st.session_state.memory_manager.archive_session(st.session_state.session_id)
            st.session_state.session_id = st.session_state.planner.create_session(st.session_state.user_id)
            st.session_state.messages = []
            instance_missing_fields()
            st.rerun()
        if st.button("👤 New User"):
            # Archive the current session if it exists
            if "session_id" in st.session_state and st.session_state.session_id is not None:
                st.session_state.memory_manager.archive_session(st.session_state.session_id)
            st.session_state.user_id = st.session_state.memory_manager.generate_unique_user_id()
            st.session_state.session_id = st.session_state.planner.create_session(st.session_state.user_id)
            st.session_state.messages = []
            instance_missing_fields()
            st.rerun()
        if st.button("🚫 Set All Sessions Inactive"):
            # Set all sessions to inactive before any further processing
            st.session_state.memory_manager.set_all_sessions_inactive()
            st.success("All sessions have been set to inactive.")
        st.markdown("---")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What would you like to know about event planning?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Send to backend system
        # Send to backend system using the new LLM flow
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                with st.spinner("🤔 Thinking..."):
                    # Get previous context for this session (or use {})
                    prev_context = st.session_state.get("session_json", {})
                    # Call the orchestrator function
                    response_text = process_user_input(
                        user_input=prompt,
                        prev_context=prev_context,
                        session_id=st.session_state.session_id,
                        user_id=st.session_state.user_id,
                        llm_client=llm_client
                    )
                    # Update session context for next turn
                    # (merge_contexts is called inside process_user_input, so you can store the merged context if you want)
                    st.session_state["session_json"] = prev_context  # Optionally update if you want to keep context
                    message_placeholder.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                error_message = f"❌ Error: {str(e)}"
                message_placeholder.error(error_message)
                st.error("Failed to get response from backend system.")

    # Display chat statistics
    if st.session_state.messages:
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Messages", len(st.session_state.messages))
        
        with col2:
            user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
            st.metric("User Messages", user_messages)
        
        with col3:
            assistant_messages = len([m for m in st.session_state.messages if m["role"] == "assistant"])
            st.metric("System Responses", assistant_messages) 