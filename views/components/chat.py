import streamlit as st

def show_chat_interface():
    # Container for chat messages
    chat_container = st.container()
    
    with chat_container:
        # Display messages in reverse order (newest first)
        for message in reversed(st.session_state.messages):
            if message["role"] == "user":
                # User message (right-aligned)
                st.markdown(
                    f"""
                    <div style='text-align: right; margin: 10px;'>
                        <div style='background-color: #e3f2fd; padding: 10px; border-radius: 10px; display: inline-block; max-width: 70%;'>
                            {message["content"]}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                # Assistant message (left-aligned)
                st.markdown(
                    f"""
                    <div style='text-align: left; margin: 10px;'>
                        <div style='background-color: #f5f5f5; padding: 10px; border-radius: 10px; display: inline-block; max-width: 70%;'>
                            {message["content"]}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                ) 