"""
OpenRouter API client for the Events Organizer Helper.
Handles communication with OpenRouter API using Pydantic models.
"""

import httpx
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from config import get_config

class ChatMessage(BaseModel):
    """Represents a single chat message."""
    
    role: str = Field(..., description="Role of the message sender (system, user, assistant)")
    content: str = Field(..., description="Content of the message")

class ChatRequest(BaseModel):
    """Request model for chat completion."""
    
    model: str = Field(..., description="Model to use for completion")
    messages: List[ChatMessage] = Field(..., description="List of chat messages")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for response")
    temperature: Optional[float] = Field(None, description="Temperature for response generation")
    stream: bool = Field(default=False, description="Whether to stream the response")

class ChatResponseChoice(BaseModel):
    """Represents a single choice in the chat response."""
    
    index: int = Field(..., description="Index of the choice")
    message: ChatMessage = Field(..., description="The response message")
    finish_reason: Optional[str] = Field(None, description="Reason for finishing")

class ChatResponseUsage(BaseModel):
    """Usage information for the API call."""
    
    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., description="Number of tokens in the completion")
    total_tokens: int = Field(..., description="Total number of tokens")

class ChatResponse(BaseModel):
    """Response model for chat completion."""
    
    id: str = Field(..., description="Response ID")
    object: str = Field(..., description="Object type")
    created: int = Field(..., description="Creation timestamp")
    model: str = Field(..., description="Model used")
    choices: List[ChatResponseChoice] = Field(..., description="Response choices")
    usage: ChatResponseUsage = Field(..., description="Usage information")

class OpenRouterClient:
    """Client for interacting with OpenRouter API."""
    
    def __init__(self):
        self.config = get_config().openrouter
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False
    ) -> ChatResponse:
        """
        Send a chat completion request to OpenRouter API.
        
        Args:
            messages: List of chat messages
            model: Model to use (defaults to config model)
            max_tokens: Maximum tokens for response (defaults to config)
            temperature: Temperature for generation (defaults to config)
            stream: Whether to stream the response
            
        Returns:
            ChatResponse object with the API response
        """
        if not self.config.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        # Use defaults from config if not provided
        model = model or self.config.model
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature or self.config.temperature
        
        # Prepare request
        request_data = ChatRequest(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=stream
        )
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://events-organizer-helper.com",
            "X-Title": "Events Organizer Helper"
        }
        
        try:
            response = await self.client.post(
                f"{self.config.base_url}/chat/completions",
                headers=headers,
                json=request_data.model_dump(exclude_none=True)
            )
            response.raise_for_status()
            
            return ChatResponse(**response.json())
            
        except httpx.HTTPStatusError as e:
            raise Exception(f"API request failed: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    async def get_models(self) -> List[Dict[str, Any]]:
        """
        Get available models from OpenRouter API.
        
        Returns:
            List of available models
        """
        if not self.config.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = await self.client.get(
                f"{self.config.base_url}/models",
                headers=headers
            )
            response.raise_for_status()
            
            return response.json().get("data", [])
            
        except httpx.HTTPStatusError as e:
            raise Exception(f"API request failed: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

# Synchronous wrapper for easier use with Streamlit
class SyncOpenRouterClient:
    """Synchronous wrapper for OpenRouter client."""
    
    def __init__(self):
        self.async_client = OpenRouterClient()
    
    def chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False
    ) -> ChatResponse:
        """Synchronous version of chat_completion."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.async_client.chat_completion(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream
            )
        )
    
    def get_models(self) -> List[Dict[str, Any]]:
        """Synchronous version of get_models."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.async_client.get_models())
    
    def close(self):
        """Close the client."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(self.async_client.close()) 