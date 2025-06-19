import streamlit as st

def show_home_page():
    # Center the content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🎉 Events Organizer Helper")
        st.markdown("""
        Welcome to the Events Organizer Helper! This intelligent assistant will help you plan and organize your events with ease.
        
        Our system can help you with:
        - Venue selection and booking
        - Catering arrangements
        - Decoration planning
        - And much more!
        
        Get started by clicking the button below to begin planning your event.
        """)
        
        # Center the button
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        if st.button("Start Planning", use_container_width=True):
            st.session_state.current_page = 'planner'
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True) 