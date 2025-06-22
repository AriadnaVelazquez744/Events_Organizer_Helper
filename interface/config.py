"""
Configuration module for the Events Organizer Helper interface.
Handles environment variables and API settings using Pydantic.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OpenRouterConfig(BaseModel):
    """Configuration for OpenRouter API connection."""
    
    api_key: str = Field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""),
        description="OpenRouter API key"
    )
    
    base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL"
    )
    
    model: str = Field(
        default="meta-llama/llama-3.3-70b-instruct:free",
        description="Default model to use for chat"
    )
    
    max_tokens: int = Field(
        default=1000,
        description="Maximum tokens for API responses"
    )
    
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for response generation (0.0-2.0)"
    )

class AppConfig(BaseModel):
    """Main application configuration."""
    
    openrouter: OpenRouterConfig = Field(
        default_factory=OpenRouterConfig,
        description="OpenRouter API configuration"
    )
    
    app_name: str = Field(
        default="Events Organizer Helper",
        description="Application name"
    )
    
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )

# Global configuration instance
config = AppConfig()

def get_config() -> AppConfig:
    """Get the current application configuration."""
    return config

def update_config(new_config: AppConfig) -> None:
    """Update the global configuration."""
    global config
    config = new_config 