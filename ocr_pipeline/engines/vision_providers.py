"""
Universal Vision Provider System

Supports multiple AI providers with a unified interface:
- Gemini (Google)
- OpenAI (GPT-4 Vision)
- Anthropic (Claude with vision)
- Ollama (Local models)
- OpenRouter (Proxy to multiple providers)
"""
from abc import ABC, abstractmethod
from typing import Optional
from PIL import Image
import base64
import io
import httpx
from config import settings


class BaseVisionProvider(ABC):
    """Abstract base class for vision providers."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    @abstractmethod
    async def analyze(self, image: Image.Image, prompt: str) -> str:
        """Analyze image with prompt and return text response."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        pass
    
    def _image_to_base64(self, image: Image.Image, format: str = "JPEG") -> str:
        """Convert PIL Image to base64."""
        buffered = io.BytesIO()
        # Resize for efficiency
        img_copy = image.copy()
        max_size = 2048
        if max(img_copy.size) > max_size:
            img_copy.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        img_copy.save(buffered, format=format, quality=85)
        return base64.b64encode(buffered.getvalue()).decode()


class GeminiProvider(BaseVisionProvider):
    """Google Gemini provider."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        super().__init__(model_name)
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(model_name)
            self.genai = genai
        except Exception as e:
            print(f"⚠️  Failed to initialize Gemini: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        return bool(settings.gemini_api_key and self.model)
    
    async def analyze(self, image: Image.Image, prompt: str) -> str:
        response = self.model.generate_content([prompt, image])
        return response.text


class OpenAIProvider(BaseVisionProvider):
    """OpenAI GPT-4 Vision provider."""
    
    def __init__(self, model_name: str = "gpt-4-vision-preview"):
        super().__init__(model_name)
        self.api_key = settings.openai_api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def analyze(self, image: Image.Image, prompt: str) -> str:
        img_b64 = self._image_to_base64(image)
        
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_b64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 4096
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        return data["choices"][0]["message"]["content"]


class AnthropicProvider(BaseVisionProvider):
    """Anthropic Claude provider."""
    
    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022"):
        super().__init__(model_name)
        self.api_key = settings.anthropic_api_key
        self.base_url = "https://api.anthropic.com/v1/messages"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def analyze(self, image: Image.Image, prompt: str) -> str:
        img_b64 = self._image_to_base64(image)
        
        payload = {
            "model": self.model_name,
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": img_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.base_url,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01"
                },
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        return data["content"][0]["text"]


class OllamaProvider(BaseVisionProvider):
    """Ollama local models provider."""
    
    def __init__(self, model_name: str = "llava:13b"):
        super().__init__(model_name)
        self.host = settings.ollama_host
    
    def is_available(self) -> bool:
        # Check if Ollama is reachable
        try:
            import httpx
            response = httpx.get(f"{self.host}/api/tags", timeout=5.0)
            return response.status_code == 200
        except:
            return False
    
    async def analyze(self, image: Image.Image, prompt: str) -> str:
        img_b64 = self._image_to_base64(image)
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [img_b64],
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_ctx": 4096,
                "num_predict": 2048
            }
        }
        
        timeout = httpx.Timeout(300.0, connect=60.0)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{self.host}/api/generate",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        return data.get("response", "").strip()


class OpenRouterProvider(BaseVisionProvider):
    """OpenRouter proxy provider."""
    
    def __init__(self, model_name: str = "anthropic/claude-3.5-sonnet"):
        super().__init__(model_name)
        self.api_key = settings.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def analyze(self, image: Image.Image, prompt: str) -> str:
        img_b64 = self._image_to_base64(image)
        
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_b64}"
                            }
                        }
                    ]
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://surya-ocr.app",
                    "X-Title": "Surya OCR"
                },
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        return data["choices"][0]["message"]["content"]


def get_vision_provider(provider: str = None, model: str = None) -> BaseVisionProvider:
    """
    Factory function to get the appropriate vision provider.
    
    Args:
        provider: Provider name (gemini, openai, anthropic, ollama, openrouter)
        model: Model name for the provider
    
    Returns:
        Initialized provider instance
    """
    provider = provider or settings.vision_provider
    
    providers = {
        "gemini": GeminiProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
        "openrouter": OpenRouterProvider
    }
    
    if provider not in providers:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(providers.keys())}")
    
    provider_class = providers[provider]
    
    # Use provider-specific default model if not specified
    if model is None:
        model_defaults = {
            "gemini": settings.gemini_model or "gemini-2.0-flash-exp",
            "openai": settings.openai_model or "gpt-4-vision-preview",
            "anthropic": settings.anthropic_model or "claude-3-5-sonnet-20241022",
            "ollama": settings.ollama_vision_model or "llava:13b",
            "openrouter": settings.openrouter_model or "anthropic/claude-3.5-sonnet"
        }
        model = model_defaults.get(provider)
    
    return provider_class(model_name=model)

