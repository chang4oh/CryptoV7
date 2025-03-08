from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    """Application settings."""
    # MeiliSearch settings
    MEILISEARCH_URL: str = Field(default="https://edge.meilisearch.com", env="MEILISEARCH_HOST")
    MEILISEARCH_MASTER_KEY: str = Field(default="", env="MEILISEARCH_MASTER_KEY")
    MEILISEARCH_SEARCH_KEY: str = Field(default="", env="MEILISEARCH_SEARCH_KEY")
    
    # MongoDB settings
    MONGODB_URI: str = Field(default="mongodb://localhost:27017", env="MONGODB_URI")
    MONGODB_DB_NAME: str = Field(default="cryptov7", env="MONGODB_DB_NAME")
    
    # Binance Testnet API settings
    BINANCE_TESTNET_API_KEY: str = Field(default="", env="BINANCE_API_KEY")
    BINANCE_TESTNET_SECRET_KEY: str = Field(default="", env="BINANCE_API_SECRET")
    BINANCE_TESTNET_BASE_URL: str = "https://testnet.binance.vision/api"
    
    # News API settings
    NEWS_API_KEY: str = Field(default="", env="NEWS_API_KEY")
    NEWS_API_BASE_URL: str = "https://newsapi.org/v2"
    
    # Hugging Face settings
    # No API key needed for open source models
    HUGGINGFACE_MODEL: str = "distilbert-base-uncased-finetuned-sst-2-english"
    
    # Add these fields to your Settings class:
    meilisearch_host: str = Field(default="http://localhost:7700", alias="MEILISEARCH_HOST")
    api_host: str = Field(default="http://localhost:8000", alias="API_HOST")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow"  # This allows extra fields from .env
    }

# Initialize settings
settings = Settings()

# Check for MEILISEARCH_HOST if MEILISEARCH_URL is not set
if not settings.MEILISEARCH_URL and os.environ.get("MEILISEARCH_HOST"):
    settings.MEILISEARCH_URL = os.environ.get("MEILISEARCH_HOST") 