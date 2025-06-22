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
    
    with st.expander("OpenRouter API Settings", expanded=True):
        # API Key input
        api_key = st.text_input(
            "OpenRouter API Key:",
            value=config.openrouter.api_key,
            type="password",
            help="Get your API key from https://openrouter.ai/keys"
        )
        
        # Test API connection
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("🔍 Test Connection"):
                if api_key:
                    test_api_connection(api_key)
                else:
                    st.error("Please enter an API key first.")
        
        with col2:
            if api_key:
                st.success("✅ API key entered")
            else:
                st.warning("⚠️ No API key configured")
        
        # Model selection
        st.subheader("Default Model")
        available_models = [
            "openai/gpt-3.5-turbo",
            "openai/gpt-4",
            "anthropic/claude-3-haiku",
            "anthropic/claude-3-sonnet",
            "meta-llama/llama-3.1-8b-instruct"
        ]
        
        default_model = st.selectbox(
            "Default Model:",
            available_models,
            index=available_models.index(config.openrouter.model)
        )
        
        # Model parameters
        st.subheader("Model Parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            default_temperature = st.slider(
                "Default Temperature:",
                min_value=0.0,
                max_value=2.0,
                value=config.openrouter.temperature,
                step=0.1
            )
        
        with col2:
            default_max_tokens = st.slider(
                "Default Max Tokens:",
                min_value=100,
                max_value=4000,
                value=config.openrouter.max_tokens,
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
        if st.button("💾 Save to Memory"):
            save_settings_to_memory(
                api_key=api_key,
                default_model=default_model,
                default_temperature=default_temperature,
                default_max_tokens=default_max_tokens,
                app_name=app_name,
                debug_mode=debug_mode
            )
    
    with col2:
        if st.button("📁 Save to .env"):
            save_settings_to_env(
                api_key=api_key,
                default_model=default_model,
                default_temperature=default_temperature,
                default_max_tokens=default_max_tokens
            )
    
    with col3:
        if st.button("🔄 Reset to Defaults"):
            reset_to_defaults()
    
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