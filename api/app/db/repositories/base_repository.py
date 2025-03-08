from typing import Any, Dict, List, Optional, TypeVar, Generic, Type
from pydantic import BaseModel
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
import logging
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.db.mongodb import MongoDB, get_database

T = TypeVar('T', bound=BaseModel)

logger = logging.getLogger(__name__)

class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, collection: str, model_class: Type[T]):
        self.collection_name = collection
        self.model_class = model_class
        self._collection = None
    
    @property
    def collection(self) -> AsyncIOMotorCollection:
        """Get the MongoDB collection, handling connection issues."""
        if self._collection is None:
            try:
                from app.db.mongodb import get_database, connect_to_mongodb
                
                # Try to get the database, connect if not already connected
                try:
                    db = get_database()
                except ConnectionError:
                    # This will either connect successfully or raise an error
                    # that will be caught and logged but not stop the application
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        loop.run_until_complete(connect_to_mongodb())
                        db = get_database()
                    except Exception as e:
                        logger.error(f"Failed to connect to MongoDB: {e}")
                        # Return None for the collection, operations will be handled safely
                        return None
                
                self._collection = db[self.collection_name]
            except Exception as e:
                logger.error(f"Failed to get MongoDB collection '{self.collection_name}': {e}")
                return None
        return self._collection
    
    async def find_one(self, query: Dict[str, Any]) -> Optional[T]:
        """Find a single document by query."""
        try:
            if not self.collection:
                logger.error("MongoDB collection not available")
                return None
                
            document = await self.collection.find_one(query)
            if document:
                # Convert ObjectId to string
                if '_id' in document and isinstance(document['_id'], ObjectId):
                    document['_id'] = str(document['_id'])
                return self.model_class(**document)
            return None
        except (ConnectionError, ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection error in find_one: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in find_one: {e}")
            return None
    
    async def find_many(
        self, 
        query: Dict[str, Any], 
        skip: int = 0, 
        limit: int = 100,
        sort: Optional[List[tuple]] = None
    ) -> List[T]:
        """Find multiple documents by query with pagination."""
        try:
            cursor = self.collection.find(query).skip(skip).limit(limit)
            
            if sort:
                cursor = cursor.sort(sort)
            
            documents = await cursor.to_list(length=limit)
            return [
                self.model_class(**{
                    **doc, 
                    '_id': str(doc['_id']) if '_id' in doc and isinstance(doc['_id'], ObjectId) else doc.get('_id')
                }) 
                for doc in documents
            ]
        except (ConnectionError, ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection error in find_many: {e}")
            return []
        except Exception as e:
            logger.error(f"Error in find_many: {e}")
            return []
    
    async def count(self, query: Dict[str, Any]) -> int:
        """Count documents matching query."""
        try:
            return await self.collection.count_documents(query)
        except (ConnectionError, ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection error in count: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error in count: {e}")
            return 0
    
    async def insert_one(self, document: T) -> Optional[str]:
        """Insert a single document."""
        try:
            doc_dict = document.model_dump(exclude_none=True, by_alias=True)
            
            # Remove id if it's None
            if '_id' in doc_dict and doc_dict['_id'] is None:
                del doc_dict['_id']
            
            result = await self.collection.insert_one(doc_dict)
            return str(result.inserted_id)
        except (ConnectionError, ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection error in insert_one: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in insert_one: {e}")
            return None
    
    async def insert_many(self, documents: List[T]) -> List[str]:
        """Insert multiple documents."""
        try:
            docs_dicts = [
                {k: v for k, v in doc.model_dump(exclude_none=True, by_alias=True).items() 
                 if not (k == '_id' and v is None)} 
                for doc in documents
            ]
            
            result = await self.collection.insert_many(docs_dicts)
            return [str(id) for id in result.inserted_ids]
        except (ConnectionError, ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection error in insert_many: {e}")
            return []
        except Exception as e:
            logger.error(f"Error in insert_many: {e}")
            return []
    
    async def update_one(
        self, 
        query: Dict[str, Any], 
        update_data: Dict[str, Any],
        upsert: bool = False
    ) -> Optional[T]:
        """Update a single document."""
        try:
            # Ensure we're using $set for updates
            update = {"$set": update_data} if "$set" not in update_data else update_data
            
            result = await self.collection.update_one(query, update, upsert=upsert)
            
            if result.modified_count > 0 or (upsert and result.upserted_id):
                return await self.find_one(query)
            return None
        except (ConnectionError, ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection error in update_one: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in update_one: {e}")
            return None
    
    async def update_many(
        self, 
        query: Dict[str, Any], 
        update_data: Dict[str, Any]
    ) -> int:
        """Update multiple documents, returns count of modified docs."""
        try:
            # Ensure we're using $set for updates
            update = {"$set": update_data} if "$set" not in update_data else update_data
            
            result = await self.collection.update_many(query, update)
            return result.modified_count
        except (ConnectionError, ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection error in update_many: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error in update_many: {e}")
            return 0
    
    async def delete_one(self, query: Dict[str, Any]) -> bool:
        """Delete a single document."""
        try:
            result = await self.collection.delete_one(query)
            return result.deleted_count > 0
        except (ConnectionError, ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection error in delete_one: {e}")
            return False
        except Exception as e:
            logger.error(f"Error in delete_one: {e}")
            return False
    
    async def delete_many(self, query: Dict[str, Any]) -> int:
        """Delete multiple documents, returns count of deleted docs."""
        try:
            result = await self.collection.delete_many(query)
            return result.deleted_count
        except (ConnectionError, ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection error in delete_many: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error in delete_many: {e}")
            return 0
    
    async def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute an aggregation pipeline."""
        try:
            cursor = self.collection.aggregate(pipeline)
            return await cursor.to_list(length=None)
        except (ConnectionError, ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection error in aggregate: {e}")
            return []
        except Exception as e:
            logger.error(f"Error in aggregate: {e}")
            return [] 