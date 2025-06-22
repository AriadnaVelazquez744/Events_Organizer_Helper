import streamlit as st
from src.agents.session_memory import SessionMemoryManager
from views.utils.models import Criterios
from views.utils.session import reset_criterios_for_new_session

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
        # Initialize criterios if not present
        if 'criterios' not in st.session_state:
            st.session_state.criterios = Criterios()
        
        # Try to convert budget to integer, removing common currency symbols
        try:
            budget_value = int(budget.replace('$', '').replace(',', '').strip())
            st.session_state.criterios.presupuesto = budget_value
            st.success(f"✅ Budget set to ${budget_value:,}")
        except ValueError:
            st.error("❌ Please enter a valid budget number (e.g., 5000)")
    
    if invites and st.button("Add Invites to Query", use_container_width=True):
        # Initialize criterios if not present
        if 'criterios' not in st.session_state:
            st.session_state.criterios = Criterios()
        
        # Try to convert invites to integer
        try:
            invites_value = int(invites.strip())
            st.session_state.criterios.guest_count = invites_value
            st.success(f"✅ Guest count set to {invites_value}")
        except ValueError:
            st.error("❌ Please enter a valid number of guests (e.g., 200)")
    
    if catering and st.button("Add Catering to Query", use_container_width=True):
        # Initialize criterios if not present
        if 'criterios' not in st.session_state:
            st.session_state.criterios = Criterios()
        
        # Initialize catering if not present
        if st.session_state.criterios.catering is None:
            from views.utils.models import Catering
            st.session_state.criterios.catering = Catering()
        
        # Add dietary options
        if st.session_state.criterios.catering.dietary_options is None:
            st.session_state.criterios.catering.dietary_options = []
        
        # Convert catering input to proper enum values
        catering_lower = catering.lower().strip()
        from views.utils.models import DietaryOption
        
        if 'vegan' in catering_lower:
            if DietaryOption.vegan not in st.session_state.criterios.catering.dietary_options:
                st.session_state.criterios.catering.dietary_options.append(DietaryOption.vegan)
        if 'vegetarian' in catering_lower:
            if DietaryOption.vegetarian not in st.session_state.criterios.catering.dietary_options:
                st.session_state.criterios.catering.dietary_options.append(DietaryOption.vegetarian)
        if 'gluten' in catering_lower:
            if DietaryOption.gluten_free not in st.session_state.criterios.catering.dietary_options:
                st.session_state.criterios.catering.dietary_options.append(DietaryOption.gluten_free)
        if 'dairy' in catering_lower:
            if DietaryOption.dairy_free not in st.session_state.criterios.catering.dietary_options:
                st.session_state.criterios.catering.dietary_options.append(DietaryOption.dairy_free)
        if 'nut' in catering_lower:
            if DietaryOption.nut_free not in st.session_state.criterios.catering.dietary_options:
                st.session_state.criterios.catering.dietary_options.append(DietaryOption.nut_free)
        
        st.success(f"✅ Catering preferences updated: {catering}")
    
    # Session Information
    st.markdown("---")
    st.markdown("<div style='font-size: 1.2em; font-weight: bold;'>Session Info</div>", unsafe_allow_html=True)
    st.markdown(f"Messages in session: {len(st.session_state.messages)}")
    
    # Show current criteria summary
    if 'criterios' in st.session_state and st.session_state.criterios:
        st.markdown("**Current Criteria:**")
        criterios = st.session_state.criterios
        if criterios.presupuesto:
            st.markdown(f"💰 Budget: ${criterios.presupuesto:,}")
        if criterios.guest_count:
            st.markdown(f"👥 Guests: {criterios.guest_count}")
        if criterios.catering and criterios.catering.dietary_options:
            st.markdown(f"🍽️ Dietary: {', '.join([opt.value for opt in criterios.catering.dietary_options])}")
    
    # Show previous criteria summary if different from current
    if 'criterios_prev' in st.session_state and st.session_state.criterios_prev:
        prev_criterios = st.session_state.criterios_prev
        if (prev_criterios.presupuesto or prev_criterios.guest_count or 
            (prev_criterios.catering and prev_criterios.catering.dietary_options)):
            st.markdown("**Previous Criteria:**")
            if prev_criterios.presupuesto:
                st.markdown(f"💰 Budget: ${prev_criterios.presupuesto:,}")
            if prev_criterios.guest_count:
                st.markdown(f"👥 Guests: {prev_criterios.guest_count}")
            if prev_criterios.catering and prev_criterios.catering.dietary_options:
                st.markdown(f"🍽️ Dietary: {', '.join([opt.value for opt in prev_criterios.catering.dietary_options])}")
    
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
        
        # 2. Clean the chat area and reset criteria
        st.session_state.messages = []
        reset_criterios_for_new_session()
        st.rerun()
    
    # Close Session Button (returns to home)
    if st.button("Close Session", use_container_width=True):
        if 'session_id' in st.session_state and st.session_state.session_id:
            memory_manager = SessionMemoryManager()
            memory_manager.archive_session(st.session_state.session_id)

        st.session_state.current_page = 'home'
        st.session_state.messages = []
        reset_criterios_for_new_session()
        st.rerun() 
