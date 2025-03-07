# News API Integration Guide

This guide explains how to troubleshoot and use the News API integration in the CryptoV7 application.

## Prerequisites

1. A valid News API key from [newsapi.org](https://newsapi.org/)
2. The CryptoV7 application set up and running

## Setting Up Your News API Key

1. Sign up for a free API key at [newsapi.org](https://newsapi.org/register)
2. Copy your API key from the account page
3. Add it to your `.env` file:

```
NEWS_API_KEY=your_news_api_key_here
```

## Testing Your News API Integration

### 1. Direct API Testing

You can test your News API key directly without the application using the `test_news_api.py` script:

```bash
python test_news_api.py
```

This script will:
- Test the direct connection to News API
- Test the application's news endpoint
- Identify any issues with your API key or sentiment analysis

### 2. Application News Endpoints

The following endpoints are available for news:

- `GET /api/news/crypto?query=cryptocurrency` - Get general cryptocurrency news
- `GET /api/news/symbol/{symbol}` - Get news for a specific cryptocurrency (e.g., BTC, ETH)

## Troubleshooting Common Issues

### "API key not configured" error

- Check that your News API key is correctly set in the `.env` file
- Make sure there are no spaces or quotes around the key

### "You have made too many requests" error

- News API has rate limits (100 requests/day for free tier)
- Use the caching feature by setting `_cache_ttl` in `news_service.py`

### "Sentiment Analysis Failed" error

This occurs when the sentiment analysis can't process the news titles. This might be due to:

1. **Missing Dependencies**:
   - Install the required dependencies:
   ```bash
   pip install numpy transformers torch
   ```

2. **Using Fallback Mode**:
   The application will automatically fall back to a rule-based sentiment analysis if the ML model can't be loaded.

## How the News Integration Works

1. **Fetching News**: The application fetches news articles from the News API based on queries like "cryptocurrency" or specific coins.

2. **Sentiment Analysis**: Each news title is analyzed for sentiment using Hugging Face models or a fallback rule-based system.

3. **Caching**: Results are cached for 5 minutes to reduce API calls.

4. **Error Handling**: The service handles API errors gracefully and provides useful error messages.

## Monitoring and Maintenance

- Check the application logs for any News API errors
- Monitor your News API usage in your [newsapi.org account](https://newsapi.org/account)
- Consider upgrading to a paid plan if you need more requests 