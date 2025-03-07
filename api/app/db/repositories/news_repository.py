from app.db.meilisearch import get_meilisearch_client

class NewsRepository:
    """Repository for news data access operations."""
    
    async def get_recent_news(self, limit=1000):
        """
        Get recent news from the database.
        
        This is a placeholder implementation. In a real application, 
        this would fetch data from MongoDB.
        """
        # Placeholder for demonstration
        return [
            {
                "_id": f"news_{i}",
                "title": f"Crypto News Article {i}",
                "content": f"This is the content of crypto news article {i}.",
                "source": "CryptoNews" if i % 2 == 0 else "BlockchainTimes",
                "publication_date": "2025-03-07T00:00:00Z",
                "sentiment_score": (i % 5) * 0.2  # 0.0 to 0.8
            }
            for i in range(10)  # Just 10 dummy news articles for example
        ]
    
    async def sync_news_to_meilisearch(self, limit=1000):
        """Synchronize recent news to MeiliSearch."""
        news_items = await self.get_recent_news(limit=limit)
        client = get_meilisearch_client()
        news_index = client.index('news_index')
        
        processed_news = [
            {
                "id": str(item["_id"]),
                "title": item["title"],
                "content": item["content"],
                "source": item["source"],
                "publication_date": item["publication_date"],
                "sentiment_score": item["sentiment_score"]
            }
            for item in news_items
        ]
        
        # Add documents to MeiliSearch
        news_index.add_documents(processed_news) 