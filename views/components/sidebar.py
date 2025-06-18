import streamlit as st
from views.utils.session import clear_session

def show_sidebar():       
    # Help Section
    st.markdown("---")
    st.subheader("Help")
    
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
    
    # Session Information
    st.markdown("---")
    st.subheader("Session Info")
    st.markdown(f"Messages in session: {len(st.session_state.messages)}")
    
    st.markdown("---")
    st.subheader("Controls")
    
    # New Session Button
    if st.button("New Session", use_container_width=True):
        clear_session()
        st.rerun()

    # Close Session Button
    if st.button("Close Session", use_container_width=True):
        st.session_state.current_page = 'home'
        clear_session()
        st.rerun() 