# MeiliSearch Setup for CryptoV7

This guide provides instructions for setting up and configuring MeiliSearch for the CryptoV7 application, supporting both local and cloud deployments.

## Setup Scripts

The following scripts are available to help you set up and manage your MeiliSearch configuration:

### 1. `fix_meilisearch_setup.py`

This is the main setup script that fixes common MeiliSearch configuration issues:

- Tests connectivity to both local and cloud instances
- Retrieves valid API keys
- Creates required indexes
- Updates environment files with proper configuration
- Creates additional utility scripts

To use it, run:

```bash
python fix_meilisearch_setup.py
```

### 2. `switch_meilisearch_config.py`

This script makes it easy to switch between local and cloud MeiliSearch configurations:

```bash
# To use local MeiliSearch
python switch_meilisearch_config.py local

# To use cloud MeiliSearch
python switch_meilisearch_config.py cloud
```

### 3. `setup_crypto_index.py`

This script sets up a sample cryptocurrency index with test data:

- Creates the "crypto" index if it doesn't exist
- Populates it with sample cryptocurrency data
- Configures optimal index settings for searching
- Sets up searchable, filterable, and sortable attributes

To use it, run:

```bash
python setup_crypto_index.py
```

### 4. `meilisearch_demo.py`

This script demonstrates common MeiliSearch operations:

- Index operations (creating, listing)
- Document operations (adding, retrieving)
- Search operations (basic search, filtering, sorting)
- Multi-search operations

To run the demo:

```bash
python meilisearch_demo.py
```

## Local vs. Cloud Configuration

### Local Setup

The local MeiliSearch configuration points to:
- URL: `http://localhost:7700`
- Master Key: The key specified in your start_meilisearch.bat file

To start the local MeiliSearch server:

```bash
./start_meilisearch.bat
```

### Cloud Setup

The cloud setup uses:
- URL: `https://ms-4ea3138ff5ca-19930.nyc.meilisearch.io`
- Admin Key: The key that has been verified to work with the cloud instance

## MeiliSearch API Operations

### Basic Operations

#### Search

```python
# Basic search
client.index("crypto").search("bitcoin")

# Search with filters
client.index("crypto").search("", {"filter": "current_price > 1000"})

# Sort results
client.index("crypto").search("", {"sort": ["market_cap:desc"]})
```

#### Documents

```python
# Add documents
index.add_documents([{"id": "1", "name": "Bitcoin", "price": 40000}])

# Get documents
index.get_documents({"limit": 10})
```

#### Indexes

```python
# Create an index
client.create_index("my_index", {"primaryKey": "id"})

# List all indexes
client.get_indexes()
```

### Advanced Settings

#### Configure index settings

```python
# Set searchable attributes
index.update_searchable_attributes(["name", "description"])

# Set filterable attributes
index.update_filterable_attributes(["price", "category"])

# Set synonyms
index.update_synonyms({
    "btc": ["bitcoin"],
    "eth": ["ethereum"]
})
```

## Troubleshooting

### Common Issues

1. **Key validation fails**:
   - Ensure you're using the correct keys for the instance you're connecting to
   - Run `fix_meilisearch_setup.py` to retrieve and configure valid keys

2. **Can't connect to MeiliSearch**:
   - Make sure the MeiliSearch server is running if using local setup
   - Check your internet connection for cloud setup
   - Verify the URL is correct in your .env file

3. **Permission errors**:
   - Make sure you're using the appropriate key for the operation:
     - Master key for administrative operations
     - Admin key for index and document management
     - Search key for search operations

4. **Search not returning expected results**:
   - Check the searchable attributes configuration
   - Ensure documents are properly indexed
   - Check your filters and search query syntax

## API Reference Links

For more information, refer to the official MeiliSearch documentation:

- [Indexes API](https://www.meilisearch.com/docs/reference/api/indexes)
- [Documents API](https://www.meilisearch.com/docs/reference/api/documents)
- [Search API](https://www.meilisearch.com/docs/reference/api/search)
- [Multi-Search API](https://www.meilisearch.com/docs/reference/api/multi_search)
- [Settings API](https://www.meilisearch.com/docs/reference/api/settings)
- [Keys API](https://www.meilisearch.com/docs/reference/api/keys)
- [Tasks API](https://www.meilisearch.com/docs/reference/api/tasks)
- [Facet Search API](https://www.meilisearch.com/docs/reference/api/facet_search) 