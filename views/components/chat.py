import streamlit as st

def show_chat_interface():
    # Container for chat messages
    chat_container = st.container()
    
    with chat_container:
        # Display messages in chronological order (oldest first)
        for message in st.session_state.messages:
            if message["role"] == "user":
                # User message (right-aligned)
                st.markdown(
                    f"""
                    <div style='text-align: right; margin: 10px;'>
                        <div style='
                            background-color: #4CAF50;
                            color: white;
                            padding: 12px 20px;
                            border-radius: 20px;
                            display: inline-block;
                            max-width: 70%;
                            margin-left: auto;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        '>
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
                        <div style='
                            background-color: #f5f5f5;
                            padding: 12px 20px;
                            border-radius: 20px;
                            display: inline-block;
                            max-width: 70%;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        '>
                            {message["content"]}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                ) 