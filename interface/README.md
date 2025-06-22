# Events Organizer Helper - Streamlit Interface

A modern, interactive web interface for the Events Organizer Helper built with Streamlit and integrated with OpenRouter API for AI-powered event planning assistance.

## 🚀 Features

- **💬 Interactive Chat Interface**: Chat with AI about event planning, venue selection, catering, decorations, and more
- **⚙️ Settings Management**: Configure API keys and customize model parameters
- **🎯 Multi-Model Support**: Choose from various AI models (GPT-3.5, GPT-4, Claude, Llama, etc.)
- **📊 Real-time Usage Tracking**: Monitor token usage and API costs
- **🔧 Easy Configuration**: Simple setup with environment variables

## 📋 Prerequisites

- Python 3.8 or higher
- OpenRouter API account and key
- Internet connection for API access

## 🛠️ Installation

1. **Navigate to the interface directory:**
   ```bash
   cd interface
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp env_example.txt .env
   ```
   
   Edit `.env` and add your OpenRouter API key:
   ```
   OPENROUTER_API_KEY=your_actual_api_key_here
   ```

## 🚀 Running the Application

1. **Start the Streamlit app:**
   ```bash
   streamlit run app.py
   ```

2. **Open your browser** and navigate to the URL shown in the terminal (usually `http://localhost:8501`)

## 📖 Usage Guide

### Chat Page 💬

The main chat interface allows you to:

- **Ask questions** about event planning, venue selection, catering, decorations, etc.
- **Choose AI models** from the sidebar (GPT-3.5, GPT-4, Claude, etc.)
- **Adjust parameters** like temperature and max tokens
- **View conversation history** and token usage statistics
- **Clear chat** to start fresh conversations

**Example prompts:**
- "Help me plan a wedding for 100 guests"
- "What should I consider when choosing a venue?"
- "Give me ideas for wedding decorations"
- "How do I create a budget for my event?"

### Settings Page ⚙️

Configure your application:

- **API Key Management**: Set and test your OpenRouter API key
- **Model Selection**: Choose your preferred AI model
- **Parameter Tuning**: Adjust temperature, max tokens, and other settings
- **Save Options**: Save settings to memory or .env file
- **Connection Testing**: Verify your API connection works

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key | Required |
| `OPENROUTER_MODEL` | Default model to use | `openai/gpt-3.5-turbo` |
| `OPENROUTER_TEMPERATURE` | Response creativity (0.0-2.0) | `0.7` |
| `OPENROUTER_MAX_TOKENS` | Maximum response length | `1000` |

### Available Models

- **OpenAI**: `openai/gpt-3.5-turbo`, `openai/gpt-4`
- **Anthropic**: `anthropic/claude-3-haiku`, `anthropic/claude-3-sonnet`
- **Meta**: `meta-llama/llama-3.1-8b-instruct`
- **And many more** available through OpenRouter

## 🏗️ Architecture

### File Structure

```
interface/
├── app.py                 # Main Streamlit application
├── config.py             # Configuration management with Pydantic
├── requirements.txt      # Python dependencies
├── env_example.txt       # Environment variables template
├── README.md            # This file
├── api/
│   ├── __init__.py
│   └── openrouter_client.py  # OpenRouter API client
└── pages/
    ├── __init__.py
    ├── chat_page.py      # Chat interface page
    └── settings_page.py  # Settings configuration page
```

### Key Components

#### 1. **Configuration Management (`config.py`)**
- Uses Pydantic for type-safe configuration
- Handles environment variables with validation
- Provides default values and error handling

#### 2. **API Client (`api/openrouter_client.py`)**
- Async HTTP client for OpenRouter API
- Pydantic models for request/response validation
- Error handling and retry logic
- Synchronous wrapper for Streamlit compatibility

#### 3. **Chat Interface (`pages/chat_page.py`)**
- Real-time chat with AI assistant
- Message history management
- Model parameter controls
- Usage statistics display

#### 4. **Settings Management (`pages/settings_page.py`)**
- API key configuration
- Model selection and parameter tuning
- Connection testing
- Settings persistence

## 🔒 Security

- API keys are stored securely in environment variables
- No sensitive data is logged or displayed
- HTTPS communication with OpenRouter API
- Input validation and sanitization

## 💰 Cost Management

- **Token Usage Tracking**: Monitor your API usage in real-time
- **Model Selection**: Choose cost-effective models for different tasks
- **Parameter Optimization**: Adjust settings to control response length
- **Usage Statistics**: View detailed usage information

## 🐛 Troubleshooting

### Common Issues

1. **"API connection failed"**
   - Check your OpenRouter API key
   - Verify you have credits in your OpenRouter account
   - Ensure internet connection is working

2. **"No API key configured"**
   - Set your API key in the Settings page
   - Or add it to your `.env` file

3. **Slow responses**
   - Try a different model
   - Reduce max_tokens setting
   - Check your internet connection

### Getting Help

- Check the OpenRouter documentation: https://openrouter.ai/docs
- Review the Streamlit documentation: https://docs.streamlit.io
- Check the application logs for detailed error messages

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is part of the Events Organizer Helper and follows the same license terms.

## 🙏 Acknowledgments

- **Streamlit** for the amazing web app framework
- **OpenRouter** for providing access to multiple AI models
- **Pydantic** for robust data validation
- **Httpx** for modern async HTTP client 