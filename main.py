"""
Unified script to:
1. Create database tables
2. Scrape RSS feeds
3. Insert articles into database
"""

import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.database.db_manager import DatabaseManager
from app.scrapers.rss_scraper import RSSFetcher, Scraper
from app.agent.agent import ArticleSummarizerAgent
from datetime import date, timedelta
from app.agent.tools import send_daily_news_email

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main_yahoo():
    """
    Yahoo News pipeline: create tables, scrape, process, insert, and summarize.
    """
    from app.scrapers.yahoo_scraper import YahooScraper, YahooRSSFetcher
    from app.database.db_manager import DatabaseManager
    from app.agent.agent import ArticleSummarizerAgent
    from app.agent.tools import send_daily_news_email
    from datetime import date, timedelta

    config_path = "config/config.json"
    days_back = 1

    print("=" * 60)
    print("Yahoo RSS Scraper - Database Pipeline")
    print("=" * 60)
    print("Note: Database connection managed by connection.py")
    print("=" * 60)

    # Step 1: Initialize database and create tables
    print("\n[Step 1] Creating database tables...")
    db_manager = DatabaseManager()
    db_manager.create_tables()

    # Step 2: Fetch RSS feeds
    print("\n[Step 2] Fetching Yahoo RSS feeds...")
    fetcher = YahooRSSFetcher(config_path=config_path)
    try:
        fetcher.fetch_all()
        print(f"✓ Fetched {len(fetcher.feeds)} Yahoo feeds")
    except Exception as e:
        print(f"✗ Error fetching Yahoo feeds: {e}")
        return

    # Step 3: Scrape articles
    print("\n[Step 3] Scraping Yahoo News articles...")
    scraper = YahooScraper(fetcher)

    today = date.today()
    start_date = today - timedelta(days=days_back)

    try:
        extraction = scraper.collect_date_range(start_date=start_date, end_date=today)
        total_articles = sum(len(col['articles']) for col in extraction['scraping'])
        total_collections = len(extraction['scraping'])

        print(f"✓ Collected {total_articles} Yahoo articles from {total_collections} sources")
        for col in extraction['scraping']:
            print(f"  - {col['source']}: {len(col['articles'])} articles")
    except Exception as e:
        print(f"✗ Error scraping Yahoo News articles: {e}")
        return

    # Step 4: Process articles with AI agent (clean markdown, summarize)
    if total_articles > 0:
        print(f"\n[Step 4] Processing Yahoo News articles with AI agent...")
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
        print(f"\n[Step 5] Inserting {total_articles} Yahoo News articles into database...")
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
    print("Yahoo News pipeline completed successfully!")
    print("=" * 60)
    recipients = db_manager.get_all_emails()
    send_daily_news_email(recipients=recipients)



if __name__ == "__main__":
    main_yahoo()