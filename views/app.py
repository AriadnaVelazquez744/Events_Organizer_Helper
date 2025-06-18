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

# Configure Streamlit page
st.set_page_config(
    page_title="Events Organizer Helper",
    page_icon="🎉",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
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

# Main navigation
def main():
    if st.session_state.current_page == 'home':
        show_home_page()
    elif st.session_state.current_page == 'planner':
        show_planner_page()

if __name__ == "__main__":
    main() 