import streamlit as st
from pathlib import Path
import sys

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import pages
from views.pages.home import show_home_page
from views.pages.planner import show_planner_page

# Import system components
from main import initialize_system
from src.agents.session_memory import SessionMemoryManager

# Configure Streamlit page
st.set_page_config(
    page_title="Events Organizer Helper",
    page_icon="🎉",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': ""
    }
)

# Hide the default navigation and page labels
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display: none;}
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 0;
        }
        section[data-testid="stSidebar"] > div:first-child > div {
            padding-top: 0;
        }
        section[data-testid="stSidebar"] > div:first-child > div > div {
            padding-top: 0;
        }
        section[data-testid="stSidebar"] > div:first-child > div > div > div {
            padding-top: 0;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'

# Initialize system components
if 'system_initialized' not in st.session_state:
    st.session_state.system_initialized = False

# Initialize user ID
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

# Initialize criterios if not present
if 'criterios' not in st.session_state:
    from views.utils.models import Criterios
    st.session_state.criterios = Criterios()

# Initialize criterios_prev if not present
if 'criterios_prev' not in st.session_state:
    from views.utils.models import Criterios
    st.session_state.criterios_prev = Criterios()

def initialize_application_system():
    """Initialize the processing system and clean session states."""
    if not st.session_state.system_initialized:
        try:
            # Initialize the processing system
            st.info("🔄 Initializing processing system...")
            system = initialize_system()
            
            # Deactivating all session states
            # st.info("🧹 Deactivating session states...")
            memory_manager = SessionMemoryManager()
            memory_manager.set_all_sessions_inactive()
            st.session_state.memory_manager = memory_manager

            planner = system["planner"]
            st.session_state.planner = planner
            
            # Generate unique user ID for this session
            if st.session_state.user_id is None:
                st.info("👤 Generating unique user ID...")
                user_id = memory_manager.generate_unique_user_id()
                st.session_state.user_id = user_id
                st.success(f"✅ User ID generated: {user_id}")
            
            # Store system components in session state
            st.session_state.system = system
            st.session_state.system_initialized = True
            
            st.success("✅ System initialized successfully!")
            
        except Exception as e:
            st.error(f"❌ Error initializing system: {str(e)}")
            st.session_state.system_initialized = False

# Main navigation
def main():
    # Initialize system on first run
    initialize_application_system()
    
    if st.session_state.current_page == 'home':
        show_home_page()
    elif st.session_state.current_page == 'planner':
        show_planner_page()

if __name__ == "__main__":
    main() 