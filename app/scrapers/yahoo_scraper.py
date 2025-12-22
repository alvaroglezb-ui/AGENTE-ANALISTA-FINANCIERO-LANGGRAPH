"""
Yahoo News scraper using feedparser to create extraction objects.
"""

import os
import json
from typing import Dict, List, Optional
from datetime import date, datetime, timedelta
import requests
import feedparser
from markdownify import markdownify as md
from dotenv import load_dotenv
from bs4 import BeautifulSoup
load_dotenv()

# Import the same TypedDict structures from rss_scraper
from app.scrapers.rss_scraper import Article, collection, extraction


class YahooRSSFetcher:
    """Fetches news from Yahoo RSS feeds using feedparser."""
    
    def __init__(self, config: Optional[Dict] = None, config_path: Optional[str] = None):
        """
        Initialize Yahoo RSS fetcher.
        
        Args:
            config: Dict with "YAHOO_RSS_URLS" key containing RSS feed mappings
            config_path: Path to JSON config file
        """
        self.config = {}
        self.feeds: Dict[str, Optional[feedparser.FeedParserDict]] = {}
        
        if config is not None:
            self.config = config
        elif config_path is not None:
            self.load_config(config_path)
        
        self.rss_urls: Dict[str, str] = self.config.get("YAHOO_RSS_URLS", {})
    
    def load_config(self, path: str):
        """Load configuration from JSON file."""
        path = os.path.expanduser(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.config = data
        self.rss_urls = self.config.get("YAHOO_RSS_URLS", {})
    
    def get_rss_urls(self) -> Dict[str, str]:
        """Get all configured Yahoo RSS URLs."""
        return self.rss_urls
    
    def fetch(self, name: str, url: Optional[str] = None) -> Optional[feedparser.FeedParserDict]:
        """
        Fetch and parse a single RSS feed.
        
        Args:
            name: Feed name identifier
            url: Optional URL override
        
        Returns:
            Parsed feed or None on failure
        """
        if url is None:
            url = self.rss_urls.get(name)
            if not url:
                raise KeyError(f"No URL for feed name: {name}")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=20, verify=False)
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
            self.feeds[name] = parsed
            return parsed
        except Exception as e:
            print(f"Error fetching Yahoo RSS feed {name}: {e}")
            self.feeds[name] = None
            return None
    
    def fetch_all(self) -> Dict[str, Optional[feedparser.FeedParserDict]]:
        """
        Fetch all feeds from config.
        
        Returns:
            Dictionary of feed name to parsed feed
        """
        for name, url in self.rss_urls.items():
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
    
    def get_entries(self, name: str, filter_date: Optional[date] = None) -> List[Dict]:
        """
        Get entries for a specific feed.
        
        Args:
            name: Feed name from config
            filter_date: Optional date to filter articles
        
        Returns:
            List of entry dictionaries (filtered to .html links only)
        """
        feed = self.feeds.get(name)
        if not feed:
            return []
        
        entries = feed.get("entries") or []
        
        # Filter for .html links only (as shown in notebook)
        html_entries = [entry for entry in entries if entry.get("link", "").endswith(".html")]
        
        if filter_date is None:
            return html_entries
        
        # Filter by date
        filtered = []
        for entry in html_entries:
            entry_date = self._parse_entry_date(entry)
            if entry_date == filter_date:
                filtered.append(entry)
        
        return filtered
    
    def get_entries_by_date_range(
        self, name: str, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> List[Dict]:
        """
        Get entries within a date range.
        
        Args:
            name: Feed name from config
            start_date: Start date for filtering
            end_date: End date for filtering
        
        Returns:
            List of entry dictionaries (filtered to .html links only)
        """
        feed = self.feeds.get(name)
        if not feed:
            return []
        
        entries = feed.get("entries") or []
        
        # Filter for .html links only
        html_entries = [entry for entry in entries if entry.get("link", "").endswith(".html")]
        
        if start_date is None and end_date is None:
            return html_entries
        
        # Filter by date range
        filtered = []
        for entry in html_entries:
            entry_date = self._parse_entry_date(entry)
            if entry_date is None:
                continue
            if start_date and entry_date < start_date:
                continue
            if end_date and entry_date > end_date:
                continue
            filtered.append(entry)
        
        return filtered


class YahooScraper:
    """Builds an `extraction` payload containing all Yahoo RSS articles."""
    
    def __init__(self, fetcher: YahooRSSFetcher):
        """
        Initialize Yahoo scraper.
        
        Args:
            fetcher: YahooRSSFetcher instance
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
        Convert a Yahoo RSS entry to an Article.
        
        Args:
            source: Source name
            entry: Yahoo RSS entry dictionary
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
    
    def _fetch_content(self, html_content: str) -> str:
        """Extrae el contenido principal del artículo de Yahoo Finance"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extraer datos del artículo
            articulo = {}
            
            # Título del artículo
            titulo = soup.find('h1')
            articulo['titulo'] = titulo.get_text(strip=True) if titulo else ''
            
            # Autor
            autor = soup.find('div', class_='author-info') or soup.find('span', class_='author')
            articulo['autor'] = autor.get_text(strip=True) if autor else ''
            
            # Fecha de publicación
            fecha = soup.find('time')
            articulo['fecha'] = fecha.get('datetime') if fecha else ''
            
            # Contenido del artículo - Yahoo Finance usa diferentes estructuras
            contenido_principal = []
            
            # Buscar el contenido en diferentes posibles contenedores
            article_body = (
                soup.find('div', class_='article-body') or 
                soup.find('div', class_='caas-body') or
                soup.find('article') or
                soup.find('div', {'data-test': 'article-body'})
            )
            
            if article_body:
                # Extraer párrafos
                parrafos = article_body.find_all('p')
                for p in parrafos:
                    texto = p.get_text(strip=True)
                    if texto and len(texto) > 50:  # Filtrar párrafos muy cortos
                        contenido_principal.append(texto)
            
            articulo['contenido'] = '\n\n'.join(contenido_principal)
            articulo['num_parrafos'] = len(contenido_principal)
            
            return articulo
        
        except Exception as e:
            print(f"Error al extraer contenido: {e}")
            return None
    

    def _fetch_html(self, url: str) -> str:
        """Obtiene el contenido HTML de una URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return response.text
        
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener {url}: {e}")
            return None
    
    def collect_feed(self, feed_name: str, filter_date: Optional[date] = None) -> collection:
        """
        Collect entries for a specific feed.
        
        Args:
            feed_name: Feed name from config
            filter_date: Optional date to filter articles
        
        Returns:
            collection TypedDict
        """
        col = self._ensure_collection(feed_name)
        entries = self.fetcher.get_entries(feed_name, filter_date)
        
        # Limit to MAX_ARTICLES if set
        max_articles = int(os.getenv("MAX_ARTICLES", "10"))
        entries = entries[:max_articles]
        
        for entry in entries:
            content = self._fetch_markdown(entry.get("link", ""))
            col["articles"].append(self._entry_to_article(feed_name, entry, content))
        
        return col
    
    def collect_all(self, filter_date: Optional[date] = None) -> extraction:
        """
        Collect entries from all feeds.
        
        Args:
            filter_date: Optional date to filter articles
        
        Returns:
            extraction TypedDict
        """
        for feed_name in self.fetcher.get_rss_urls().keys():
            self.collect_feed(feed_name, filter_date)
        return self.data
    
    def collect_date_range(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> extraction:
        """
        Collect entries from all feeds within a date range.
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
        
        Returns:
            extraction TypedDict
        """
        for feed_name in self.fetcher.get_rss_urls().keys():
            entries = self.fetcher.get_entries_by_date_range(feed_name, start_date, end_date)
            col = self._ensure_collection(feed_name)
            
            # Limit to MAX_ARTICLES if set
            max_articles = int(os.getenv("MAX_ARTICLES", "10"))
            entries = entries[:max_articles]
            
            for entry in entries:
                html = self._fetch_html(entry.get("link", ""))
                articulo = self._fetch_content(html)
                content = articulo['contenido'] 
                col["articles"].append(self._entry_to_article(feed_name, entry, content))

        return self.data
    

