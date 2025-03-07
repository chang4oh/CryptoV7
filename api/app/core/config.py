from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    """Application settings."""
    # MeiliSearch settings
    MEILISEARCH_URL: str = Field(default="https://edge.meilisearch.com", env="MEILISEARCH_HOST")
    MEILISEARCH_MASTER_KEY: str = Field(default="", env="MEILISEARCH_MASTER_KEY")
    MEILISEARCH_SEARCH_KEY: str = Field(default="", env="MEILISEARCH_SEARCH_KEY")
    
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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Allow extra fields from the .env file
        extra = "ignore"

# Initialize settings
settings = Settings()

# Check for MEILISEARCH_HOST if MEILISEARCH_URL is not set
if not settings.MEILISEARCH_URL and os.environ.get("MEILISEARCH_HOST"):
    settings.MEILISEARCH_URL = os.environ.get("MEILISEARCH_HOST") 