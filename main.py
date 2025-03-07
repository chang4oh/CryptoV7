import meilisearch
import json
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_meilisearch_connection():
    """Test the MeiliSearch connection and basic functionality."""
    try:
        # Get MeiliSearch connection details from environment variables
        meilisearch_url = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
        meilisearch_key = os.getenv("MEILISEARCH_MASTER_KEY")
        
        if not meilisearch_key:
            print("Error: MEILISEARCH_MASTER_KEY is not set in the .env file.")
            return False
        
        print(f"Connecting to MeiliSearch at {meilisearch_url}")
        client = meilisearch.Client(meilisearch_url, meilisearch_key)
        
        # Check health
        health = client.health()
        print(f"MeiliSearch health: {health}")
        
        # Check if movies.json exists
        if not os.path.exists('movies.json'):
            # Create a sample movies.json file
            sample_movies = [
                {
                    "id": "1",
                    "title": "Batman Begins",
                    "poster": "https://example.com/batman.jpg",
                    "overview": "Bruce Wayne returns to Gotham after years abroad to fight crime.",
                    "release_date": "2005-06-15"
                },
                {
                    "id": "2",
                    "title": "The Dark Knight",
                    "poster": "https://example.com/dark_knight.jpg",
                    "overview": "Batman faces his greatest challenge yet as he takes on the Joker.",
                    "release_date": "2008-07-18"
                }
            ]
            
            with open('movies.json', 'w', encoding='utf-8') as f:
                json.dump(sample_movies, f, indent=2)
                
            print("Created sample movies.json file")
        
        # Load the movies data
        with open('movies.json', encoding='utf-8') as json_file:
            movies = json.load(json_file)
            
        # Add documents to the index
        try:
            task = client.index('movies').add_documents(movies)
            print(f"Documents added successfully. Task ID: {task.task_uid if hasattr(task, 'task_uid') else task}")
            return True
        except meilisearch.errors.MeiliSearchApiError as e:
            print(f"MeiliSearch API error: {e}")
            print("This might be due to an authentication issue. Make sure your master key is correct.")
            return False
    
    except Exception as e:
        print(f"Error connecting to MeiliSearch: {e}")
        return False

if __name__ == "__main__":
    success = test_meilisearch_connection()
    if success:
        print("\nMeiliSearch is properly configured and working!")
        sys.exit(0)
    else:
        print("\nThere were issues with the MeiliSearch setup. Please check the errors above.")
        sys.exit(1)