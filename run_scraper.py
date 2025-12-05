"""
Unified script to:
1. Create database tables
2. Scrape RSS feeds
3. Insert articles into database
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.database.db_manager import DatabaseManager
from app.scrapers.rss_scraper import RSSFetcher, Scraper
from app.agent.agent import ArticleSummarizerAgent
from datetime import date, timedelta
from app.agent.tools import  send_daily_news_email


def main():
    """Main execution flow: create tables, scrape, insert."""
    
    # Configuration
    # Database connection is managed by app/database/connection.py
    # - Uses SQLite by default (sqlite:///rss_articles.db)
    # - For PostgreSQL, set environment variables in .env file:
    #   POSTGRES_USER=your_user
    #   POSTGRES_PASSWORD=your_password
    #   POSTGRES_HOST=localhost
    #   POSTGRES_PORT=5432
    #   POSTGRES_DB=your_database
    config_path = "config/config.json"
    days_back = 20  # Number of days to scrape back
    
    print("=" * 60)
    print("RSS Scraper - Database Pipeline")
    print("=" * 60)
    print("Note: Database connection managed by connection.py")
    print("=" * 60)
    
    # Step 1: Initialize database and create tables
    print("\n[Step 1] Creating database tables...")
    db_manager = DatabaseManager()
    db_manager.create_tables()
    
    # Step 2: Fetch RSS feeds
    print("\n[Step 2] Fetching RSS feeds...")
    fetcher = RSSFetcher(config_path=config_path)
    try:
        fetcher.fetch_all()
        print(f"✓ Fetched {len(fetcher.feeds)} feeds")
    except Exception as e:
        print(f"✗ Error fetching feeds: {e}")
        return
    
    # Step 3: Scrape articles
    print("\n[Step 3] Scraping articles...")
    scraper = Scraper(fetcher)
    
    today = date.today()
    start_date = today - timedelta(days=days_back)
    
    try:
        result = scraper.collect_date_range(start_date=start_date, end_date=today)
        
        total_articles = sum(len(col['articles']) for col in result['scraping'])
        total_collections = len(result['scraping'])
        
        print(f"✓ Collected {total_articles} articles from {total_collections} sources")
        
        # Show summary by source
        for col in result['scraping']:
            print(f"  - {col['source']}: {len(col['articles'])} articles")
            
    except Exception as e:
        print(f"✗ Error scraping articles: {e}")
        return
    
    # Step 4: Process articles with AI agent (clean markdown and summarize)
    if total_articles > 0:
        print(f"\n[Step 4] Processing articles with AI agent...")
        print("  - Cleaning markdown content")
        print("  - Generating structured summaries for non-experts")
        try:
            agent = ArticleSummarizerAgent()
            result = agent.process_extraction(result)
            print("✓ Articles processed and summarized")
        except Exception as e:
            print(f"✗ Error processing articles: {e}")
            print("Continuing without summaries...")
    
    # Step 5: Insert into database
    if total_articles > 0:
        print(f"\n[Step 5] Inserting {total_articles} articles into database...")
        try:
            extraction_id = db_manager.insert_extraction(result)
            print(f"✓ Successfully inserted extraction ID: {extraction_id}")
        except Exception as e:
            print(f"✗ Error inserting into database: {e}")
            return
    else:
        print("\n[Step 5] No articles to insert.")
        return
    
    # Step 6: Display database summary
    print("\n[Step 6] Database Summary:")
    try:
        collections = db_manager.get_collections()
        print(f"  Total collections: {len(collections)}")
        total_db_articles = sum(col['article_count'] for col in collections)
        print(f"  Total articles in database: {total_db_articles}")
        
        for col in collections:
            print(f"    - {col['source']}: {col['article_count']} articles")
    except Exception as e:
        print(f"✗ Error querying database: {e}")
    
    print("\n" + "=" * 60)
    print("Pipeline completed successfully!")
    print("=" * 60)

def main_google():
    """
    Pipeline for Google News scraping, AI processing, and DB insertion.
    """
    from app.scrapers.google_news_scraper import GoogleNewsFetcher
    from app.database.db_manager import DatabaseManager

    print("\n" + "=" * 60)
    print("Google News Pipeline Starting...")
    print("=" * 60)
    print("Note: Database connection managed by connection.py")
    print("=" * 60)
    
    # Step 1: Initialize database and create tables
    print("\n[Step 1] Creating database tables...")
    db_manager = DatabaseManager()
    db_manager.create_tables()
    
    # Step 2: Load config and initialize GoogleNewsFetcher
    print("\n[Step 2] Loading config and initializing GoogleNewsFetcher")
    try:
        fetcher = GoogleNewsFetcher(config_path="config/config.json")
        topics = fetcher.get_topics()
        if not topics:
            print("✗ No topics found in config.")
            return
        print(f"Configured Google News topics: {list(topics.keys())}")
    except Exception as e:
        print(f"✗ Error initializing GoogleNewsFetcher: {e}")
        return

    # Step 3: Collect articles for all topics
    print("\n[Step 3] Collecting Google News articles...")
    extraction = {"scraping": []}
    total_articles = 0

    try:
        for topic, topic_name in topics.items():
            articles = fetcher.search(topic)
            total_articles += len(articles)
            col = {
                "source": f"GoogleNews:{topic}",
                "articles": [],
            }
            for entry in articles:
                # Required structure
                col["articles"].append({
                    "title": entry.get("title", ""),
                    "source": f"GoogleNews:{topic}",
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "content": entry.get("content", ""),
                    "summary": "",    # to be filled later
                })
            extraction["scraping"].append(col)
        print(f"✓ Collected {total_articles} Google News articles")
        for col in extraction["scraping"]:
            print(f"  - {col['source']}: {len(col['articles'])} articles")
    except Exception as e:
        print(f"✗ Error scraping Google News articles: {e}")
        return

    # Step 4: Process articles with AI agent (clean markdown, summarize)
    if total_articles > 0:
        print(f"\n[Step 4] Processing Google News articles with AI agent...")
        print("  - Cleaning markdown content")
        print("  - Generating structured summaries for non-experts")
        try:
            agent = ArticleSummarizerAgent()
            extraction = agent.process_extraction(extraction)
            print("✓ Articles processed and summarized")
        except Exception as e:
            print(f"✗ Error processing articles: {e}")
            print("Continuing without summaries...")

    # Step 5: Insert into database
    if total_articles > 0:
        print(f"\n[Step 5] Inserting {total_articles} Google News articles into database...")
        try:
            extraction_id = db_manager.insert_extraction(extraction)
            print(f"✓ Successfully inserted extraction ID: {extraction_id}")
        except Exception as e:
            print(f"✗ Error inserting into database: {e}")
            return
    else:
        print("\n[Step 5] No articles to insert.")
        return

    # Step 6: Display database summary
    print("\n[Step 6] Database Summary:")
    try:
        collections = db_manager.get_collections()
        print(f"  Total collections: {len(collections)}")
        total_db_articles = sum(col['article_count'] for col in collections)
        print(f"  Total articles in database: {total_db_articles}")

        for col in collections:
            print(f"    - {col['source']}: {col['article_count']} articles")
    except Exception as e:
        print(f"✗ Error querying database: {e}")

    print("\n" + "=" * 60)
    print("Google News pipeline completed successfully!")
    print("=" * 60)
    send_daily_news_email(recipients=["alvaroglezb@gmail.com"])

if __name__ == "__main__":
    main_google()
