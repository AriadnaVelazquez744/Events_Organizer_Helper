"""
Settings page for the Events Organizer Helper.
Allows users to configure API keys and application settings.
"""

import streamlit as st
import os
from config import get_config, update_config, AppConfig, OpenRouterConfig
from api.openrouter_client import SyncOpenRouterClient

def settings_page():
    """Main settings page function."""
    
    st.title("⚙️ Settings")
    st.markdown("Configure your API keys and application preferences.")
    
    # Get current configuration
    config = get_config()
    
    # API Configuration Section
    st.header("🔑 API Configuration")
    
    # --- OpenRouter Section (commented for clarity) ---
    # with st.expander("OpenRouter API Settings", expanded=True):
    #     api_key = st.text_input(
    #         "OpenRouter API Key:",
    #         value=config.openrouter.api_key,
    #         type="password",
    #         help="Get your API key from https://openrouter.ai/keys"
    #     )
    #     ...
    #     # Model selection
    #     st.subheader("Default Model")
    #     available_models = [
    #         "openai/gpt-3.5-turbo",
    #         "openai/gpt-4",
    #         "anthropic/claude-3-haiku",
    #         "anthropic/claude-3-sonnet",
    #         "meta-llama/llama-3.1-8b-instruct"
    #     ]
    #     default_model = st.selectbox(
    #         "Default Model:",
    #         available_models,
    #         index=available_models.index(config.openrouter.model)
    #     )
    #     ...
    #     # Model parameters
    #     st.subheader("Model Parameters")
    #     col1, col2 = st.columns(2)
    #     with col1:
    #         default_temperature = st.slider(
    #             "Default Temperature:",
    #             min_value=0.0,
    #             max_value=2.0,
    #             value=config.openrouter.temperature,
    #             step=0.1
    #         )
    #     with col2:
    #         default_max_tokens = st.slider(
    #             "Default Max Tokens:",
    #             min_value=100,
    #             max_value=4000,
    #             value=config.openrouter.max_tokens,
    #             step=100
    #         )

    # --- Fireworks Section ---
    with st.expander("Fireworks API Settings", expanded=True):
        fw_api_key = st.text_input(
            "Fireworks API Key:",
            value=config.fireworks.api_key,
            type="password",
            help="Get your API key from https://fireworks.ai/keys"
        )
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔍 Test Fireworks Connection"):
                if fw_api_key:
                    test_fireworks_api_connection(fw_api_key)
                else:
                    st.error("Please enter a Fireworks API key first.")
        with col2:
            if fw_api_key:
                st.success("✅ API key entered")
            else:
                st.warning("⚠️ No API key configured")
        st.subheader("Default Model")
        fireworks_models = [
            "accounts/fireworks/models/llama-v3p3-70b-instruct",
            "accounts/fireworks/models/llama-v3p1-8b-instruct",
            "accounts/fireworks/models/llama-v2-70b-chat",
            "accounts/fireworks/models/mixtral-8x7b-instruct"
        ]
        fw_default_model = st.selectbox(
            "Default Fireworks Model:",
            fireworks_models,
            index=fireworks_models.index(config.fireworks.model) if config.fireworks.model in fireworks_models else 0
        )
        st.subheader("Model Parameters")
        col1, col2 = st.columns(2)
        with col1:
            fw_default_temperature = st.slider(
                "Default Temperature:",
                min_value=0.0,
                max_value=2.0,
                value=config.fireworks.temperature,
                step=0.1
            )
        with col2:
            fw_default_max_tokens = st.slider(
                "Default Max Tokens:",
                min_value=100,
                max_value=4000,
                value=config.fireworks.max_tokens,
                step=100
            )
    
    # Application Settings Section
    st.header("🎯 Application Settings")
    
    with st.expander("General Settings", expanded=True):
        app_name = st.text_input(
            "Application Name:",
            value=config.app_name
        )
        
        debug_mode = st.checkbox(
            "Enable Debug Mode",
            value=config.debug,
            help="Enable additional logging and debug information"
        )
    
    # Save Settings
    st.header("💾 Save Settings")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 Save Fireworks to Memory"):
            save_fireworks_settings_to_memory(
                api_key=fw_api_key,
                default_model=fw_default_model,
                default_temperature=fw_default_temperature,
                default_max_tokens=fw_default_max_tokens,
                app_name=app_name,
                debug_mode=debug_mode
            )
    
    with col2:
        if st.button("📁 Save Fireworks to .env"):
            save_fireworks_settings_to_env(
                api_key=fw_api_key,
                default_model=fw_default_model,
                default_temperature=fw_default_temperature,
                default_max_tokens=fw_default_max_tokens
            )
    
    with col3:
        if st.button("�� Reset Fireworks to Defaults"):
            reset_fireworks_to_defaults()
    
    # Information Section
    st.header("ℹ️ Information")
    
    with st.expander("About OpenRouter", expanded=False):
        st.markdown("""
        **OpenRouter** is a unified API that provides access to various AI models including:
        
        - **OpenAI Models**: GPT-3.5-turbo, GPT-4
        - **Anthropic Models**: Claude-3-Haiku, Claude-3-Sonnet
        - **Meta Models**: Llama-3.1-8b-instruct
        - **And many more...**
        
        To get started:
        1. Visit [OpenRouter](https://openrouter.ai)
        2. Create an account
        3. Generate an API key
        4. Add credits to your account
        5. Use the API key in this application
        
        **Pricing**: OpenRouter offers competitive pricing and you only pay for what you use.
        """)
    
    with st.expander("API Usage Tips", expanded=False):
        st.markdown("""
        **Best Practices:**
        
        - Start with GPT-3.5-turbo for cost-effective conversations
        - Use GPT-4 for complex reasoning tasks
        - Adjust temperature based on your needs:
          - 0.0-0.3: Factual, consistent responses
          - 0.4-0.7: Balanced creativity and accuracy
          - 0.8-1.0: More creative and varied responses
        
        **Cost Optimization:**
        - Monitor your token usage
        - Use shorter prompts when possible
        - Set appropriate max_tokens limits
        - Consider using cheaper models for simple tasks
        """)

def test_api_connection(api_key: str):
    """Test the OpenRouter API connection."""
    try:
        # Create a temporary client for testing
        test_client = SyncOpenRouterClient()
        
        # Test with a simple message
        test_message = [
            {
                "role": "user",
                "content": "Hello! This is a test message."
            }
        ]
        
        with st.spinner("Testing API connection..."):
            response = test_client.chat_completion(
                messages=[{"role": "user", "content": "Hello! This is a test message."}],
                model="openai/gpt-3.5-turbo",
                max_tokens=50
            )
        
        st.success("✅ API connection successful!")
        st.info(f"Response: {response.choices[0].message.content}")
        
        # Test getting models
        models = test_client.get_models()
        st.success(f"✅ Available models: {len(models)} models found")
        
    except Exception as e:
        st.error(f"❌ API connection failed: {str(e)}")
        st.error("Please check your API key and try again.")

def save_settings_to_memory(**kwargs):
    """Save settings to application memory."""
    try:
        # Create new configuration
        new_openrouter_config = OpenRouterConfig(
            api_key=kwargs.get('api_key', ''),
            model=kwargs.get('default_model', 'openai/gpt-3.5-turbo'),
            temperature=kwargs.get('default_temperature', 0.7),
            max_tokens=kwargs.get('default_max_tokens', 1000)
        )
        
        new_config = AppConfig(
            openrouter=new_openrouter_config,
            app_name=kwargs.get('app_name', 'Events Organizer Helper'),
            debug=kwargs.get('debug_mode', False)
        )
        
        # Update global configuration
        update_config(new_config)
        
        st.success("✅ Settings saved to memory!")
        
    except Exception as e:
        st.error(f"❌ Failed to save settings: {str(e)}")

def save_settings_to_env(**kwargs):
    """Save settings to .env file."""
    try:
        env_content = f"""# Events Organizer Helper Configuration
OPENROUTER_API_KEY={kwargs.get('api_key', '')}
OPENROUTER_MODEL={kwargs.get('default_model', 'openai/gpt-3.5-turbo')}
OPENROUTER_TEMPERATURE={kwargs.get('default_temperature', 0.7)}
OPENROUTER_MAX_TOKENS={kwargs.get('default_max_tokens', 1000)}
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        st.success("✅ Settings saved to .env file!")
        
    except Exception as e:
        st.error(f"❌ Failed to save to .env: {str(e)}")

def reset_to_defaults():
    """Reset settings to default values."""
    try:
        default_config = AppConfig()
        update_config(default_config)
        
        st.success("✅ Settings reset to defaults!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Failed to reset settings: {str(e)}")

# --- Fireworks helpers ---
def test_fireworks_api_connection(api_key: str):
    from interface.api.fireworks_client import SyncFireworksClient, ChatMessage
    try:
        test_client = SyncFireworksClient()
        test_message = [ChatMessage(role="user", content="Hello! This is a test message.")]
        with st.spinner("Testing Fireworks API connection..."):
            response = test_client.chat_completion(
                messages=test_message,
                model="accounts/fireworks/models/llama-v3p3-70b-instruct",
                max_tokens=50
            )
        st.success("✅ Fireworks API connection successful!")
        st.info(f"Response: {response.choices[0].message.content}")
        models = test_client.get_models()
        st.success(f"✅ Available models: {len(models)} models found")
    except Exception as e:
        st.error(f"❌ Fireworks API connection failed: {str(e)}")
        st.error("Please check your Fireworks API key and try again.")

def save_fireworks_settings_to_memory(**kwargs):
    from config import AppConfig, FireworksConfig, get_config, update_config
    try:
        new_fireworks_config = FireworksConfig(
            api_key=kwargs.get('api_key', ''),
            model=kwargs.get('default_model', 'accounts/fireworks/models/llama-v3p3-70b-instruct'),
            temperature=kwargs.get('default_temperature', 0.7),
            max_tokens=kwargs.get('default_max_tokens', 1000)
        )
        current_config = get_config()
        new_config = AppConfig(
            openrouter=current_config.openrouter,
            fireworks=new_fireworks_config,
            app_name=kwargs.get('app_name', 'Events Organizer Helper'),
            debug=kwargs.get('debug_mode', False)
        )
        update_config(new_config)
        st.success("✅ Fireworks settings saved to memory!")
    except Exception as e:
        st.error(f"❌ Failed to save Fireworks settings: {str(e)}")

def save_fireworks_settings_to_env(**kwargs):
    try:
        env_content = f"""# Fireworks Configuration\nFIREWORKS_API_KEY={kwargs.get('api_key', '')}\nFIREWORKS_MODEL={kwargs.get('default_model', 'accounts/fireworks/models/llama-v3p3-70b-instruct')}\nFIREWORKS_TEMPERATURE={kwargs.get('default_temperature', 0.7)}\nFIREWORKS_MAX_TOKENS={kwargs.get('default_max_tokens', 1000)}\n"""
        with open('.env', 'w') as f:
            f.write(env_content)
        st.success("✅ Fireworks settings saved to .env file!")
    except Exception as e:
        st.error(f"❌ Failed to save Fireworks settings to .env: {str(e)}")

def reset_fireworks_to_defaults():
    from config import AppConfig, FireworksConfig, get_config, update_config
    try:
        current_config = get_config()
        default_fireworks_config = FireworksConfig()
        new_config = AppConfig(
            openrouter=current_config.openrouter,
            fireworks=default_fireworks_config,
            app_name=current_config.app_name,
            debug=current_config.debug
        )
        update_config(new_config)
        st.success("✅ Fireworks settings reset to defaults!")
    except Exception as e:
        st.error(f"❌ Failed to reset Fireworks settings: {str(e)}") 