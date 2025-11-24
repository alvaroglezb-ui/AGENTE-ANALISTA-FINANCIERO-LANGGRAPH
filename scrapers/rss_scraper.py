import os
import json
from pathlib import Path
from typing import Dict, Optional, Any, TypedDict, List
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
                 timeout: int = 10, session: Optional[requests.Session] = None):
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
        except Exception:
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

    def get_entries(self, name: str) -> list:
        """
        Return list of entries for a feed name (empty list if none).
        """
        feed = self.feeds.get(name)
        if not feed:
            return []
        # Entries can sometimes be under 'item' as well as 'entries'
        return feed.get("entries") or feed.get("item") or []

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

    def iter_entries(self, name: str):
        """
        Generator yielding (published, title, link, entry_dict) for each entry in feed.
        """
        for entry in self.get_entries(name):
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

    def collect_feed(self, feed_name: str) -> collection:
        col = self._ensure_collection(feed_name)
        for entry in self.fetcher.get_entries(feed_name):
            content = self._fetch_markdown(entry.get("link", ""))
            col["articles"].append(self._entry_to_article(feed_name, entry, content))
        return col

    def collect_all(self) -> extraction:
        for feed_name in self.fetcher.get_feed_urls().keys():
            self.collect_feed(feed_name)
        return self.data


if __name__ == "__main__":
    fetcher = RSSFetcher(config_path="config/config.json")
    fetcher.fetch_all()
    scraper = Scraper(fetcher)
    result = scraper.collect_all()

    articles_dir = Path("articles")
    articles_dir.mkdir(exist_ok=True)

    for col in result["scraping"]:
        print(f"Fuente: {col['source']} - artículos: {len(col['articles'])}")
        for idx, article in enumerate(col["articles"], 1):
            preview = article["content"][:200].replace("\n", " ")
            print(f"  #{idx}: {article['title']} -> {preview}...")
            filename = articles_dir / f"{col['source']}_{idx}.txt"
            with filename.open("w", encoding="utf-8") as fh:
                fh.write(article["content"])

