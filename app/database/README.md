# Database Module

This module provides SQLAlchemy models and database management for storing RSS articles.

## Structure

### Models (`models.py`)

Three SQLAlchemy models based on the TypedDict classes:

1. **Article**: Represents a single RSS article
   - `id`: Primary key
   - `title`: Article title
   - `source`: RSS feed source name
   - `link`: Article URL (unique)
   - `published`: Publication date string
   - `content`: Markdown content of the article
   - `collection_id`: Foreign key to Collection
   - `created_at`: Timestamp when inserted

2. **Collection**: Groups articles by RSS source
   - `id`: Primary key
   - `source`: Source name (unique)
   - `created_at`: Timestamp when created
   - `updated_at`: Timestamp when last updated
   - `articles`: Relationship to Article objects

3. **Extraction**: Container for scraping sessions
   - `id`: Primary key
   - `created_at`: Timestamp when extraction was performed
   - `collections`: Relationship to Collection objects

### Database Manager (`db_manager.py`)

The `DatabaseManager` class handles:

- **Table Creation**: Automatically creates all tables on initialization
- **Data Insertion**: Inserts articles from `extraction` TypedDict structure
- **Querying**: Methods to retrieve articles and collections

## Usage

### Basic Example

```python
from scrapers.rss_scraper import RSSFetcher, Scraper
from database.db_manager import DatabaseManager
from datetime import date, timedelta

# 1. Initialize database (creates tables)
db = DatabaseManager(database_url="sqlite:///rss_articles.db")

# 2. Scrape RSS feeds
fetcher = RSSFetcher(config_path="config/config.json")
fetcher.fetch_all()
scraper = Scraper(fetcher)

# 3. Collect articles
today = date.today()
result = scraper.collect_date_range(
    start_date=today - timedelta(days=7),
    end_date=today
)

# 4. Save to database
extraction_id = scraper.save_to_database()
```

### Using DatabaseManager Directly

```python
from database.db_manager import DatabaseManager

db = DatabaseManager()

# Insert extraction data
extraction_id = db.insert_extraction(extraction_data)

# Query collections
collections = db.get_collections()
for col in collections:
    print(f"{col['source']}: {col['article_count']} articles")

# Query articles
articles = db.get_articles_by_source("MSCI_WORLD_NEWS_ULR")
for article in articles:
    print(f"{article.title} - {article.link}")
```

## Database URLs

### SQLite (Default)
```python
db = DatabaseManager("sqlite:///rss_articles.db")
```

### PostgreSQL
```python
db = DatabaseManager("postgresql://user:password@localhost/rss_db")
```

### MySQL
```python
db = DatabaseManager("mysql+pymysql://user:password@localhost/rss_db")
```

## Features

- **Automatic Table Creation**: Tables are created automatically on first use
- **Duplicate Prevention**: Articles are not inserted if they already exist (based on link)
- **Relationships**: Proper foreign key relationships between models
- **Timestamps**: Automatic tracking of creation and update times

