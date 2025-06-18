import streamlit as st
from views.utils.session import clear_session

def show_sidebar():       
    # Help Section
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div style='font-size: 1.2em; font-weight: bold;'>Help</div>", unsafe_allow_html=True)
    
    with st.expander("How to use the planner"):
        st.markdown("""
        1. Type your event planning needs in the text area
        2. The system will process your request and respond
        3. You can provide additional information when asked
        4. Use the sidebar to manage your session
        """)
    
    with st.expander("Example queries"):
        st.markdown("""
        - "I need to plan a wedding for 100 people"
        - "What venues are available for a corporate event?"
        - "Help me plan the catering for my birthday party"
        """)
    
    # Budget Input Section
    st.markdown("---")
    st.markdown("<div style='font-size: 1.2em; font-weight: bold;'>Budget</div>", unsafe_allow_html=True)
    budget = st.text_input("Enter your budget (e.g., $5000)", key="budget_input")
    
    if budget and st.button("Add Budget to Query", use_container_width=True):
        # Add budget to the current query
        if 'current_query' not in st.session_state:
            st.session_state.current_query = ""
        st.session_state.current_query += f"\nBudget: {budget}"
    
    # Session Information
    st.markdown("---")
    st.markdown("<div style='font-size: 1.2em; font-weight: bold;'>Session Info</div>", unsafe_allow_html=True)
    st.markdown(f"Messages in session: {len(st.session_state.messages)}")
    
    st.markdown("---")
    st.markdown("<div style='font-size: 1.2em; font-weight: bold;'>Controls</div>", unsafe_allow_html=True)
    
    # New Session Button (only clears the planner page)
    if st.button("New Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_query = ""
        st.rerun()
    
    # Close Session Button (returns to home)
    if st.button("Close Session", use_container_width=True):
        st.session_state.current_page = 'home'
        clear_session()
        st.rerun() 