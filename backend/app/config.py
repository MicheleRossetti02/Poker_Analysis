"""
Configuration settings for the Poker SaaS backend.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    
    # App
    app_name: str = "Poker SaaS API"
    debug: bool = True
    
    # API
    api_prefix: str = "/api"
    
    # Equity calculation
    monte_carlo_iterations: int = 10000
    
    # Database (future)
    postgres_url: str = ""
    mongodb_url: str = ""
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
