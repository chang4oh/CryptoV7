from fastapi import BackgroundTasks
from app.db.repositories.trades_repository import TradesRepository
from app.db.repositories.news_repository import NewsRepository

async def schedule_meilisearch_sync(background_tasks: BackgroundTasks):
    """Schedule MeiliSearch synchronization tasks."""
    background_tasks.add_task(sync_trades)
    background_tasks.add_task(sync_news)

async def sync_trades():
    """Sync trades data to MeiliSearch."""
    trades_repo = TradesRepository()
    await trades_repo.sync_trades_to_meilisearch()

async def sync_news():
    """Sync news data to MeiliSearch."""
    news_repo = NewsRepository()
    await news_repo.sync_news_to_meilisearch() 