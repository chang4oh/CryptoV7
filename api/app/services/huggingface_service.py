import logging
from app.core.config import settings
import sys
import importlib.util

logger = logging.getLogger(__name__)

# Check for NumPy availability
def is_numpy_available():
    return importlib.util.find_spec("numpy") is not None

# Check for transformers availability
def is_transformers_available():
    return importlib.util.find_spec("transformers") is not None

# Check for torch availability
def is_torch_available():
    return importlib.util.find_spec("torch") is not None

# Perform dependency checks
NUMPY_AVAILABLE = is_numpy_available()
TRANSFORMERS_AVAILABLE = is_transformers_available()
TORCH_AVAILABLE = is_torch_available()

if not NUMPY_AVAILABLE:
    logger.warning("NumPy is not available. Sentiment analysis will use fallback mode.")
if not TRANSFORMERS_AVAILABLE:
    logger.warning("Transformers library is not available. Sentiment analysis will use fallback mode.")
if not TORCH_AVAILABLE:
    logger.warning("PyTorch is not available. Sentiment analysis will use fallback mode.")

class HuggingFaceService:
    """Service for using Hugging Face models locally."""
    
    def __init__(self):
        self.model_name = settings.HUGGINGFACE_MODEL
        self._sentiment_pipeline = None
        self._dependencies_checked = False
        self._dependencies_available = False
        
        # Initialize dependency status
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if all required dependencies are available."""
        if self._dependencies_checked:
            return self._dependencies_available
            
        required_deps = [
            ("numpy", NUMPY_AVAILABLE),
            ("transformers", TRANSFORMERS_AVAILABLE),
            ("torch", TORCH_AVAILABLE)
        ]
        
        missing_deps = [name for name, available in required_deps if not available]
        
        if missing_deps:
            logger.warning(f"Missing dependencies for sentiment analysis: {', '.join(missing_deps)}")
            logger.warning("Install them with: pip install " + " ".join(missing_deps))
            self._dependencies_available = False
        else:
            logger.info("All dependencies for sentiment analysis are available")
            self._dependencies_available = True
            
        self._dependencies_checked = True
        return self._dependencies_available
    
    def _get_dummy_pipeline(self):
        """Return a dummy pipeline that simulates sentiment analysis."""
        def dummy_pipeline(texts):
            if not isinstance(texts, list):
                texts = [texts]
                
            results = []
            for text in texts:
                # Simple rule-based fallback for positive/negative detection
                lower_text = text.lower()
                positive_words = ["good", "great", "excellent", "bullish", "rally", "gain", "positive", "up", "rise", "growth"]
                negative_words = ["bad", "poor", "terrible", "bearish", "crash", "loss", "negative", "down", "fall", "drop"]
                
                positive_count = sum(1 for word in positive_words if word in lower_text)
                negative_count = sum(1 for word in negative_words if word in lower_text)
                
                if positive_count > negative_count:
                    sentiment = {"label": "POSITIVE", "score": 0.75}
                elif negative_count > positive_count:
                    sentiment = {"label": "NEGATIVE", "score": 0.75}
                else:
                    sentiment = {"label": "NEUTRAL", "score": 0.5}
                
                # Add explanation for fallback mode
                if not self._dependencies_available:
                    missing_deps = []
                    if not NUMPY_AVAILABLE:
                        missing_deps.append("NumPy")
                    if not TRANSFORMERS_AVAILABLE:
                        missing_deps.append("Transformers")
                    if not TORCH_AVAILABLE:
                        missing_deps.append("PyTorch")
                    
                    sentiment["fallback_mode"] = True
                    sentiment["missing_dependencies"] = missing_deps
                
                results.append(sentiment)
            
            return results
        
        return dummy_pipeline
    
    @property
    def sentiment_pipeline(self):
        """Lazy-load the sentiment analysis pipeline."""
        if self._sentiment_pipeline is None:
            # Check if dependencies are available
            if not self._check_dependencies():
                logger.warning("Using fallback sentiment analysis due to missing dependencies")
                self._sentiment_pipeline = self._get_dummy_pipeline()
                return self._sentiment_pipeline
            
            try:
                # Try to import and use the transformer pipeline
                from transformers import pipeline
                logger.info(f"Loading sentiment analysis model: {self.model_name}")
                
                # Try to suppress warnings
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    self._sentiment_pipeline = pipeline("sentiment-analysis", model=self.model_name)
                
                logger.info("Sentiment analysis model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading sentiment analysis model: {e}")
                logger.info("Falling back to dummy pipeline")
                self._sentiment_pipeline = self._get_dummy_pipeline()
        
        return self._sentiment_pipeline
    
    def analyze_sentiment(self, texts):
        """Analyze sentiment of text(s)."""
        if not texts:
            return []
        
        if isinstance(texts, str):
            texts = [texts]
            
        try:
            results = self.sentiment_pipeline(texts)
            
            # If using fallback mode, results already have the interpretation
            if isinstance(results, list) and results and "fallback_mode" not in results[0]:
                # Add interpretation
                for result in results:
                    if "label" in result:
                        if result["label"] == "POSITIVE":
                            result["interpretation"] = "Bullish"
                        elif result["label"] == "NEGATIVE":
                            result["interpretation"] = "Bearish"
                        else:
                            result["interpretation"] = "Neutral"
            
            return results
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            # Return dummy responses with error information
            return [
                {
                    "label": "ERROR", 
                    "score": 0.0, 
                    "error": str(e),
                    "interpretation": "Neutral"
                } 
                for _ in texts
            ]
    
    def analyze_crypto_news(self, news_titles):
        """Analyze sentiment of crypto news titles."""
        return self.analyze_sentiment(news_titles)

# Create a singleton instance
huggingface_service = HuggingFaceService() 