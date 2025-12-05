"""
Example script demonstrating how to:
1. Create database tables
2. Scrape RSS feeds
3. Insert articles into database

Note: Database connection is managed by app.database.connection
- Uses SQLite by default
- For PostgreSQL, set environment variables in .env file
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.scrapers.rss_scraper import RSSFetcher, Scraper
from app.database.db_manager import DatabaseManager
from datetime import date, timedelta

def main():
    # Step 1: Initialize database and create tables
    print("Step 1: Creating database tables...")
    print("Note: Connection managed by app.database.connection")
    db_manager = DatabaseManager()
    db_manager.create_tables()
    
    # Step 2: Fetch and scrape RSS feeds
    print("\nStep 2: Fetching RSS feeds...")
    fetcher = RSSFetcher(config_path="config/config.json")
    fetcher.fetch_all()
    
    scraper = Scraper(fetcher)
    
    # Step 3: Collect articles (last 7 days)
    print("\nStep 3: Collecting articles...")
    today = date.today()
    week_ago = today - timedelta(days=7)
    result = scraper.collect_date_range(start_date=week_ago, end_date=today)
    
    total_articles = sum(len(col['articles']) for col in result['scraping'])
    print(f"Collected {total_articles} articles from {len(result['scraping'])} sources")
    
    # Step 4: Insert articles into database
    print("\nStep 4: Inserting articles into database...")
    extraction_id = scraper.save_to_database()
    print(f"✓ Extraction saved with ID: {extraction_id}")
    
    # Step 5: Query database
    print("\nStep 5: Querying database...")
    collections = db_manager.get_collections()
    print(f"\nCollections in database:")
    for col in collections:
        print(f"  - {col['source']}: {col['article_count']} articles")
    
    # Get articles from a specific source
    if collections:
        source_name = collections[0]['source']
        print(f"\nSample articles from '{source_name}':")
        articles = db_manager.get_articles_by_source(source_name)
        for article in articles[:3]:  # Show first 3
            print(f"  - {article.title}")
            print(f"    Link: {article.link}")
            print(f"    Published: {article.published}")

if __name__ == "__main__":
    main()

