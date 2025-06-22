import streamlit as st
from pages.chat_page import chat_page
from pages.settings_page import settings_page

# Configure the main app
st.set_page_config(
    page_title="Events Organizer Helper",
    page_icon="🎉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define pages
pages = {
    "💬 Chat with AI": chat_page,
    "⚙️ Settings": settings_page
}

# Sidebar navigation
st.sidebar.title("🎉 Events Organizer Helper")
st.sidebar.markdown("---")

# Page selection
selected_page = st.sidebar.selectbox(
    "Choose a page:",
    list(pages.keys())
)

# Display selected page
pages[selected_page]()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Powered by OpenRouter API**") 