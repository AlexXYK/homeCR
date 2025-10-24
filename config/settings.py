"""
Centralized configuration management for the OCR system.
Uses pydantic-settings for type-safe configuration from environment variables.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Ollama Configuration
    ollama_host: str = "http://192.168.0.153:11434"
    ollama_vision_model: str = "llava:13b"  # Multimodal model for vision tasks
    ollama_text_model: str = "gemma3:12b-it-qat"  # Text-only model for formatting
    ollama_formatter_model: str = "gemma3:12b-it-qat"  # Text-only model for formatting
    ollama_max_parallel_requests: int = 2
    
    # Vision Provider Configuration
    vision_provider: str = "ollama"  # Options: gemini, openai, anthropic, ollama, openrouter
    
    # Provider API Keys
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    
    # Provider-Specific Models
    gemini_model: str = "gemini-2.0-flash-exp"  # gemini-2.0-flash-exp, gemini-1.5-flash, gemini-1.5-pro
    openai_model: str = "gpt-4-vision-preview"  # gpt-4-vision-preview, gpt-4-turbo
    anthropic_model: str = "claude-3-5-sonnet-20241022"  # claude-3-5-sonnet, claude-3-opus
    openrouter_model: str = "anthropic/claude-3.5-sonnet"  # Any OpenRouter model
    
    # Default OCR Settings
    use_hybrid_ocr: bool = True  # Run both Tesseract + Surya in parallel
    perfect_tables: bool = False  # Use vision provider specifically for perfect table formatting
    
    # API Configuration
    api_port: int = 5000
    dashboard_port: int = 8080
    
    # Agent System
    enable_autonomous_agents: bool = True
    require_approval_for_changes: bool = True
    max_concurrent_agent_tasks: int = 2
    agent_pause_on_user_request: bool = True
    
    # Dashboard
    enable_auth: bool = False
    
    # Commercial Features
    enable_api_keys: bool = False
    enable_rate_limiting: bool = False
    
    # Database
    database_url: str = "sqlite:///./data/ocr_system.db"
    test_results_db: str = "sqlite:///./data/test_results.db"
    
    # Logging
    log_level: str = "INFO"
    
    # OCR Engine Configuration
    tesseract_confidence_threshold: float = 60.0
    surya_confidence_threshold: float = 0.7
    vision_model_confidence_threshold: float = 0.8
    
    # Classification thresholds
    handwriting_threshold: float = 0.6
    table_heavy_threshold: float = 0.5
    low_quality_threshold: float = 0.4


# Global settings instance
settings = Settings()

