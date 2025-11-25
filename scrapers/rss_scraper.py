import os
import json
from pathlib import Path
from typing import Dict, Optional, Any, TypedDict, List
from datetime import datetime, date, timedelta
import requests
import feedparser
import html2text
from markdownify import markdownify as md

class Article(TypedDict):
    """Single normalized RSS entry."""

    title: str
    source: str
    link: str
    published: str
    content: str


class collection(TypedDict):
    """Articles grouped by their RSS identifier."""

    source: str
    articles: List[Article]


class extraction(TypedDict):
    """Container for the full scraping result."""

    scraping: List[collection]

class RSSFetcher:
    def __init__(self, config: Optional[Dict[str, str]] = None, config_path: Optional[str] = None,
                 timeout: int = 20, session: Optional[requests.Session] = None):
        """
        Provide either config (dict with "RSS_URLS") or config_path to a JSON file.
        """
        self.timeout = timeout
        self.session = session or requests.Session()
        self.config = {}
        if config is not None:
            self.config = config
        elif config_path is not None:
            self.load_config(config_path)
        self.feeds: Dict[str, Optional[feedparser.FeedParserDict]] = {}

    def load_config(self, path: str):
        path = os.path.expanduser(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.config = data

    def get_feed_urls(self) -> Dict[str, str]:
        return self.config.get("RSS_URLS", {})

    def fetch(self, name: str, url: Optional[str] = None) -> Optional[feedparser.FeedParserDict]:
        """
        Fetch and parse a single feed. Returns parsed feed or None on failure.
        """
        if url is None:
            urls = self.get_feed_urls()
            url = urls.get(name)
            if not url:
                raise KeyError(f"No URL for feed name: {name}")
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            parsed = feedparser.parse(resp.content)
        except Exception as e:
            raise Exception(f"Error fetching feed {name}: {e}")
            parsed = None
        self.feeds[name] = parsed
        return parsed

    def fetch_all(self) -> Dict[str, Optional[feedparser.FeedParserDict]]:
        """
        Fetch all feeds from config and store results in self.feeds.
        """
        urls = self.get_feed_urls()
        for name, url in urls.items():
            self.fetch(name, url)
        return self.feeds

    @staticmethod
    def _parse_entry_date(entry: feedparser.FeedParserDict) -> Optional[date]:
        """Extract date from entry, returning a date object or None."""
        # Try published_parsed first (feedparser's parsed date)
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return date(*entry.published_parsed[:3])
        # Try updated_parsed as fallback
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            return date(*entry.updated_parsed[:3])
        # Try parsing the published string manually
        pub_str = entry.get("published") or entry.get("pubDate") or ""
        if pub_str:
            try:
                # Use feedparser to parse the date string
                parsed_entry = feedparser.parse(f"<item><pubDate>{pub_str}</pubDate></item>")
                if parsed_entry.entries and hasattr(parsed_entry.entries[0], "published_parsed"):
                    parsed_date = parsed_entry.entries[0].published_parsed
                    if parsed_date:
                        return date(*parsed_date[:3])
            except Exception:
                pass
        return None

    def get_entries(self, name: str, filter_date: Optional[date] = None) -> list:
        """
        Return list of entries for a feed name (empty list if none).
        Optionally filter by a specific date.
        """
        feed = self.feeds.get(name)
        if not feed:
            return []
        # Entries can sometimes be under 'item' as well as 'entries'
        entries = feed.get("entries") or feed.get("item") or []
        if filter_date is None:
            return entries
        filtered = []
        for entry in entries:
            entry_date = self._parse_entry_date(entry)
            if entry_date == filter_date:
                filtered.append(entry)
        return filtered

    def get_entries_by_date_range(
        self, name: str, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> list:
        """Get entries within a date range (inclusive)."""
        feed = self.feeds.get(name)
        if not feed:
            return []
        entries = feed.get("entries") or feed.get("item") or []
        if start_date is None and end_date is None:
            return entries
        filtered = []
        for entry in entries:
            entry_date = self._parse_entry_date(entry)
            if entry_date is None:
                continue
            if start_date and entry_date < start_date:
                continue
            if end_date and entry_date > end_date:
                continue
            filtered.append(entry)
        return filtered

    def summarize(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Return a dictionary summary for one feed (if name provided) or all feeds.
        Summary for each feed: {"entries": n, "title": feed_title}
        """
        out = {}
        targets = [name] if name else list(self.get_feed_urls().keys())
        for n in targets:
            feed = self.feeds.get(n)
            if feed and feed.get("entries"):
                out[n] = {
                    "entries": len(feed["entries"]),
                    "title": feed.get("feed", {}).get("title")
                }
            else:
                out[n] = {"entries": 0, "title": None}
        return out

    def iter_entries(self, name: str, filter_date: Optional[date] = None):
        """
        Generator yielding (published, title, link, entry_dict) for each entry in feed.
        Optionally filter by a specific date.
        """
        for entry in self.get_entries(name, filter_date):
            pub = entry.get("published") or entry.get("pubDate") or ""
            title = entry.get("title") or ""
            link = entry.get("link") or ""
            yield pub, title, link, entry


class Scraper:
    """Builds an `extraction` payload containing all RSS articles."""

    def __init__(self, fetcher: RSSFetcher):
        self.fetcher = fetcher
        self.data: extraction = {"scraping": []}
        self._html_parser = html2text.HTML2Text()
        self._html_parser.ignore_links = False
        self._html_parser.ignore_images = True
        self._html_parser.body_width = 0

    def _ensure_collection(self, source: str) -> collection:
        for col in self.data["scraping"]:
            if col["source"] == source:
                return col
        new_col: collection = {"source": source, "articles": []}
        self.data["scraping"].append(new_col)
        return new_col

    @staticmethod
    def _entry_to_article(source: str, entry: feedparser.FeedParserDict, content: str) -> Article:
        return Article(
            title=entry.get("title") or "",
            source=source,
            link=entry.get("link") or "",
            published=entry.get("published") or entry.get("pubDate") or "",
            content=content,
        )

    def _fetch_markdown(self, url: str) -> str:
        if not url:
            return ""
        try:
            response = requests.get(url)
            html_content = response.text
            markdown_content = md(html_content)
            return markdown_content
        except Exception:
            return ""

    def collect_feed(self, feed_name: str, filter_date: Optional[date] = None) -> collection:
        """Collect entries for a specific feed, optionally filtered by date."""
        col = self._ensure_collection(feed_name)
        for entry in self.fetcher.get_entries(feed_name, filter_date):
            content = self._fetch_markdown(entry.get("link", ""))
            col["articles"].append(self._entry_to_article(feed_name, entry, content))
        return col

    def collect_all(self, filter_date: Optional[date] = None) -> extraction:
        """Collect entries from all feeds, optionally filtered by date."""
        for feed_name in self.fetcher.get_feed_urls().keys():
            self.collect_feed(feed_name, filter_date)
        return self.data

    def collect_date_range(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> extraction:
        """Collect entries from all feeds within a date range."""
        for feed_name in self.fetcher.get_feed_urls().keys():
            entries = self.fetcher.get_entries_by_date_range(feed_name, start_date, end_date)
            col = self._ensure_collection(feed_name)
            for entry in entries:
                content = self._fetch_markdown(entry.get("link", ""))
                col["articles"].append(self._entry_to_article(feed_name, entry, content))
        return self.data


if __name__ == "__main__":
    fetcher = RSSFetcher(config_path="config/config.json")
    fetcher.fetch_all()
    scraper = Scraper(fetcher)
    
    # Example: Filter by today's date
    today = date.today()
    #result: extraction = scraper.collect_all(filter_date=today)
    
    # Example: Filter by date range (last 7 days)
    # from datetime import timedelta
    # week_ago = today - timedelta(days=7)
    result = scraper.collect_date_range(start_date=today-timedelta(days=3), end_date=today)
    print(result)
    # Example: Get all entries (no filter)
    #result: extraction = scraper.collect_all()
    
    