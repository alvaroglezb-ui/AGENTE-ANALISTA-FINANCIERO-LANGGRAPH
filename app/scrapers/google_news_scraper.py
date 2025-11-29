"""
Google News scraper using pygooglenews to create extraction objects.
"""

import os
import json
from typing import Dict, List, Optional
from datetime import date, datetime, timedelta
import requests
from markdownify import markdownify as md
from pygooglenews import GoogleNews

# Import the same TypedDict structures from rss_scraper
from app.scrapers.rss_scraper import Article, collection, extraction


class GoogleNewsFetcher:
    """Fetches news from Google News using pygooglenews."""
    
    def __init__(self, config: Optional[Dict] = None, config_path: Optional[str] = None):
        """
        Initialize Google News fetcher.
        
        Args:
            config: Dict with "GOOGLE_NEWS_TOPICS" key containing topic mappings
            config_path: Path to JSON config file
        """
        self.gn = GoogleNews(lang='en', country='US')
        self.config = {}
        
        if config is not None:
            self.config = config
        elif config_path is not None:
            self.load_config(config_path)
        
        self.topics: Dict[str, str] = self.config.get("GOOGLE_NEWS_TOPICS", {})
    
    def load_config(self, path: str):
        """Load configuration from JSON file."""
        path = os.path.expanduser(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.config = data
    
    def get_topics(self) -> Dict[str, str]:
        """Get all configured topics."""
        return self.topics
    
    def search(self, query: str, when: Optional[str] = None) -> List[Dict]:
        """
        Search Google News for a query.
        
        Args:
            query: Search query string
            when: Time period ('1d', '7d', '1m', '1y', or None for all)
        
        Returns:
            List of article dictionaries
        """
        try:
            if when:
                results = self.gn.search(query, when=when)
            else:
                results = self.gn.search(query)
            
            articles = results.get('entries', [])
            return articles
        except Exception as e:
            print(f"Error searching Google News for '{query}': {e}")
            return []
    
    def get_entries(self, topic_name: str, filter_date: Optional[date] = None) -> List[Dict]:
        """
        Get entries for a specific topic.
        
        Args:
            topic_name: Name of the topic from config
            filter_date: Optional date to filter articles
        
        Returns:
            List of article dictionaries
        """
        if topic_name not in self.topics:
            print(f"Warning: Topic '{topic_name}' not found in config")
            return []
        
        query = topic_name  # Use topic name as search query
        
        # Always use 1 day time frame
        articles = self.search(query, when='1d')
        
        # Filter by date if provided
        if filter_date:
            filtered = []
            for article in articles:
                published = article.get('published_parsed')
                if published:
                    article_date = date(published.tm_year, published.tm_mon, published.tm_mday)
                    if article_date >= filter_date:
                        filtered.append(article)
            return filtered
        
        return articles
    
    def get_entries_by_date_range(
        self, topic_name: str, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> List[Dict]:
        """
        Get entries within a date range. Uses 1 day time frame by default.
        
        Args:
            topic_name: Name of the topic from config
            start_date: Start date for filtering (defaults to yesterday)
            end_date: End date for filtering (defaults to today)
        
        Returns:
            List of article dictionaries
        """
        if topic_name not in self.topics:
            print(f"Warning: Topic '{topic_name}' not found in config")
            return []
        
        query = topic_name
        
        # Default to last 1 day if no dates provided
        if start_date is None or end_date is None:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=1)
        
        # Always use 1 day time frame for Google News search
        articles = self.search(query, when='1d')
        
        # Filter by date range
        filtered = []
        for article in articles:
            published = article.get('published_parsed')
            if published:
                article_date = date(published.tm_year, published.tm_mon, published.tm_mday)
                
                if start_date and article_date < start_date:
                    continue
                if end_date and article_date > end_date:
                    continue
                
                filtered.append(article)
        
        return filtered


class GoogleNewsScraper:
    """Builds an `extraction` payload containing all Google News articles."""
    
    def __init__(self, fetcher: GoogleNewsFetcher):
        """
        Initialize Google News scraper.
        
        Args:
            fetcher: GoogleNewsFetcher instance
        """
        self.fetcher = fetcher
        self.data: extraction = {"scraping": []}
    
    def _ensure_collection(self, source: str) -> collection:
        """Ensure a collection exists for the given source."""
        for col in self.data["scraping"]:
            if col["source"] == source:
                return col
        new_col: collection = {"source": source, "articles": []}
        self.data["scraping"].append(new_col)
        return new_col
    
    @staticmethod
    def _entry_to_article(source: str, entry: Dict, content: str, summary: str = "") -> Article:
        """
        Convert a Google News entry to an Article.
        
        Args:
            source: Source name
            entry: Google News entry dictionary
            content: Article content (markdown)
            summary: Article summary (default empty)
        
        Returns:
            Article TypedDict
        """
        # Parse published date
        published_str = ""
        if entry.get('published_parsed'):
            pub_parsed = entry['published_parsed']
            published_str = f"{pub_parsed.tm_year}-{pub_parsed.tm_mon:02d}-{pub_parsed.tm_mday:02d}"
        elif entry.get('published'):
            published_str = entry['published']
        
        return Article(
            title=entry.get("title", ""),
            source=source,
            link=entry.get("link", ""),
            published=published_str,
            content=content,
            summary=summary,
        )
    
    def _fetch_markdown(self, url: str) -> str:
        """
        Fetch article content and convert to markdown.
        
        Args:
            url: Article URL
        
        Returns:
            Markdown content string
        """
        if not url:
            return ""
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            html_content = response.text
            markdown_content = md(html_content)
            return markdown_content
        except Exception as e:
            print(f"Error fetching content from {url}: {e}")
            return ""
    
    def collect_topic(self, topic_name: str, filter_date: Optional[date] = None) -> collection:
        """
        Collect entries for a specific topic.
        
        Args:
            topic_name: Topic name from config
            filter_date: Optional date to filter articles
        
        Returns:
            collection TypedDict
        """
        source_name = self.fetcher.topics.get(topic_name, topic_name)
        col = self._ensure_collection(source_name)
        
        entries = self.fetcher.get_entries(topic_name, filter_date)
        for entry in entries:
            content = self._fetch_markdown(entry.get("link", ""))
            col["articles"].append(self._entry_to_article(source_name, entry, content))
        
        return col
    
    def collect_all(self, filter_date: Optional[date] = None) -> extraction:
        """
        Collect entries from all topics.
        
        Args:
            filter_date: Optional date to filter articles
        
        Returns:
            extraction TypedDict
        """
        for topic_name in self.fetcher.get_topics().keys():
            self.collect_topic(topic_name, filter_date)
        return self.data
    
    def collect_date_range(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> extraction:
        """
        Collect entries from all topics within a date range.
        Defaults to last 1 day (yesterday to today) if no dates provided.
        
        Args:
            start_date: Start date for filtering (defaults to yesterday)
            end_date: End date for filtering (defaults to today)
        
        Returns:
            extraction TypedDict
        """
        # Default to last 1 day if no dates provided
        if start_date is None or end_date is None:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=1)
        
        for topic_name in self.fetcher.get_topics().keys():
            entries = self.fetcher.get_entries_by_date_range(topic_name, start_date, end_date)
            source_name = self.fetcher.topics.get(topic_name, topic_name)
            col = self._ensure_collection(source_name)
            
            for entry in entries:
                content = self._fetch_markdown(entry.get("link", ""))
                col["articles"].append(self._entry_to_article(source_name, entry, content))
        
        return self.data
