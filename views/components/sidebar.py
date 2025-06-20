import streamlit as st
from src.agents.session_memory import SessionMemoryManager

def show_sidebar():       
    # Help Section
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div style='font-size: 1.2em; font-weight: bold;'>Help</div>", unsafe_allow_html=True)
    
    with st.expander("How to use the planner"):
        st.markdown("""
        1. Type your event planning needs in the text area, basic requirements for proper processing are available budget and number of guests. 
        2. The system will process your request and respond.
        3. You can provide additional information when asked or to give more details.
        4. Use the sidebar to manage your session and include required fields.
        """)
    
    with st.expander("Example queries"):
        st.markdown("""
        - "I need to plan a wedding for 100 people and can destine to it 30000$"
        - "I want a wedding for 300 that counts with a vegan catering in a farm, my budget is 30000$"
        - "I want a classic wedding with a budget of 15000$ and 50 guests"
        """)
    
    # Budget Input Section
    st.markdown("---")
    st.markdown("<div style='font-size: 1.0em; font-weight: bold;'>Budget</div>", unsafe_allow_html=True)
    budget = st.text_input("The budget for the event is: (e.g., $5000)", key="budget_input")

    st.markdown("<div style='font-size: 1.0em; font-weight: bold;'>Invites amount</div>", unsafe_allow_html=True)
    invites = st.text_input("How many persons go to the event? (e.g., 200)", key="invites_input")

    st.markdown("<div style='font-size: 1.0em; font-weight: bold;'>Catering</div>", unsafe_allow_html=True)
    catering = st.text_input("Diet preference: (e.g., vegan, gluten-free)", key="catering_input")
    
    
    if budget and st.button("Add Budget to Query", use_container_width=True):
        # Add budget to the current query
        if 'current_query' not in st.session_state:
            st.session_state.current_query = ""
        st.session_state.current_query += f"\nBudget: {budget}"
    if invites and st.button("Add Invites to Query", use_container_width=True):
        # Add budget to the current query
        if 'current_query' not in st.session_state:
            st.session_state.current_query = ""
        st.session_state.current_query += f"\ngest_count: {invites}"
    if budget and st.button("Add Catering to Query", use_container_width=True):
        # Add budget to the current query
        if 'current_query' not in st.session_state:
            st.session_state.current_query = ""
        st.session_state.current_query += f"\nMeal_type: {catering}"
    
    # Session Information
    st.markdown("---")
    st.markdown("<div style='font-size: 1.2em; font-weight: bold;'>Session Info</div>", unsafe_allow_html=True)
    st.markdown(f"Messages in session: {len(st.session_state.messages)}")
    
    st.markdown("---")
    st.markdown("<div style='font-size: 1.2em; font-weight: bold;'>Controls</div>", unsafe_allow_html=True)
    
    # New Session Button (only clears the planner page)
    if st.button("New Session", use_container_width=True):
        if 'session_id' in st.session_state and st.session_state.session_id:
            memory_manager = SessionMemoryManager()
            
            # 1. Archive the current session
            memory_manager.archive_session(st.session_state.session_id)
            
            # Get user_id from the session state
            user_id = st.session_state.get("user_id")

            if user_id:
                # 3. Create a new session for the same user
                new_session_id = st.session_state.planner.create_session(user_id=user_id)
                st.session_state.session_id = new_session_id
        
        # 2. Clean the chat area
        st.session_state.messages = []
        st.session_state.current_query = ""
        st.rerun()
    
    # Close Session Button (returns to home)
    if st.button("Close Session", use_container_width=True):
        if 'session_id' in st.session_state and st.session_state.session_id:
            memory_manager = SessionMemoryManager()
            memory_manager.archive_session(st.session_state.session_id)

        st.session_state.current_page = 'home'
        st.session_state.messages = []
        st.session_state.current_query = ""
        st.session_state.user_requirements = ""
        st.rerun() 