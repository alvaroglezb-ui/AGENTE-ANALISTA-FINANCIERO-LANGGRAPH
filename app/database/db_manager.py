from typing import Optional, List
from datetime import datetime, date
from app.database.connection import get_engine, get_session
from app.database.models import Base, Article, Collection, Extraction
from app.scrapers.rss_scraper import extraction as ExtractionType


class DatabaseManager:
    """Manages database operations for RSS articles using connection.py."""

    def __init__(self):
        """
        Initialize database manager using connection from connection.py.
        Connection is managed by connection.py module.
        """
        self.engine = get_engine()

    def create_tables(self):
        """
        Create all tables based on SQLAlchemy models.
        Uses the engine from connection.py.
        """
        Base.metadata.create_all(self.engine)
        print("✓ Database tables created successfully")

    def get_session(self):
        """
        Get a new database session.
        Uses get_session() from connection.py.
        """
        return get_session()

    def insert_extraction(self, extraction_data: ExtractionType) -> int:
        """
        Insert all articles from extraction data structure.
        
        Args:
            extraction_data: extraction TypedDict containing scraping results
            
        Returns:
            ID of the created extraction record
        """
        session = self.get_session()
        try:
            # Create extraction record
            extraction = Extraction()
            session.add(extraction)
            session.flush()  # Get the extraction ID

            # Process each collection
            for collection_data in extraction_data.get("scraping", []):
                source = collection_data.get("source", "")
                
                # Get or create collection
                collection = session.query(Collection).filter_by(source=source).first()
                if not collection:
                    collection = Collection(source=source, extraction_id=extraction.id)
                    session.add(collection)
                    session.flush()
                else:
                    # Update existing collection to link to this extraction
                    collection.extraction_id = extraction.id

                # Insert articles
                for article_data in collection_data.get("articles", []):
                    # Check if article already exists (by link)
                    existing_article = session.query(Article).filter_by(
                        link=article_data.get("link", "")
                    ).first()
                    
                    if not existing_article:
                        article = Article(
                            title=article_data.get("title", ""),
                            source=article_data.get("source", ""),
                            link=article_data.get("link", ""),
                            published=article_data.get("published", ""),
                            content=article_data.get("content", ""),
                            summary=article_data.get("summary", ""),
                            collection_id=collection.id
                        )
                        session.add(article)
                    else:
                        # Update existing article with summary if provided
                        if article_data.get("summary"):
                            existing_article.summary = article_data.get("summary", "")
                        if article_data.get("content"):
                            existing_article.content = article_data.get("content", "")

            session.commit()
            print(f"✓ Inserted extraction with {len(extraction_data.get('scraping', []))} collections")
            return extraction.id

        except Exception as e:
            session.rollback()
            print(f"✗ Error inserting extraction: {e}")
            raise
        finally:
            session.close()

    def get_all_articles(self, limit: Optional[int] = None):
        """Retrieve all articles from database."""
        session = self.get_session()
        try:
            query = session.query(Article).order_by(Article.created_at.desc())
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def get_articles_by_source(self, source: str):
        """Retrieve articles filtered by source."""
        session = self.get_session()
        try:
            return session.query(Article).filter_by(source=source).all()
        finally:
            session.close()

    def get_collections(self):
        """Retrieve all collections with article counts."""
        session = self.get_session()
        try:
            collections = session.query(Collection).all()
            result = []
            for col in collections:
                article_count = session.query(Article).filter_by(collection_id=col.id).count()
                result.append({
                    "id": col.id,
                    "source": col.source,
                    "article_count": article_count,
                    "created_at": col.created_at
                })
            return result
        finally:
            session.close()

    def _format_summary_html(self, summary_text: str) -> str:
        """
        Convert structured summary text to formatted HTML.
        
        Args:
            summary_text: Plain text summary with structure:
                OVERVIEW: ...
                KEY POINTS:
                • point 1
                • point 2
                WHY IT MATTERS: ...
                SIMPLE EXPLANATION: ...
        
        Returns:
            Formatted HTML string
        """
        if not summary_text:
            return ""
        
        html_parts = []
        lines = summary_text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # OVERVIEW section
            if line.startswith('OVERVIEW:'):
                content_parts = [line.replace('OVERVIEW:', '').strip()]
                i += 1
                # Collect content until next section or empty line
                while i < len(lines):
                    next_line = lines[i].strip()
                    if next_line.startswith(('KEY POINTS:', 'WHY IT MATTERS:', 'SIMPLE EXPLANATION:')):
                        break
                    if not next_line and content_parts:
                        break
                    if next_line:
                        content_parts.append(next_line)
                    i += 1
                content = ' '.join(content_parts).strip()
                if content:
                    html_parts.append(f'<div style="margin-bottom: 12px;"><strong style="color: #1e3a8a;">Overview:</strong> {content}</div>')
                continue
            
            # KEY POINTS section
            elif line.startswith('KEY POINTS:'):
                html_parts.append('<div style="margin-bottom: 12px;"><strong style="color: #1e3a8a;">Key Points:</strong><ul style="margin: 8px 0; padding-left: 20px;">')
                i += 1
                # Collect bullet points
                while i < len(lines):
                    bullet_line = lines[i].strip()
                    if bullet_line.startswith('•') or bullet_line.startswith('-'):
                        # Remove bullet characters from anywhere in the string
                        point = bullet_line.replace('•', '').replace('-', '').strip()
                        if point:
                            html_parts.append(f'<li style="margin-bottom: 6px; line-height: 1.5;">{point}</li>')
                    elif bullet_line and not bullet_line.startswith(('WHY IT MATTERS:', 'SIMPLE EXPLANATION:', 'OVERVIEW:')):
                        # Handle points without bullet prefix - still remove any bullet chars
                        point = bullet_line.replace('•', '').replace('-', '').strip()
                        if point:
                            html_parts.append(f'<li style="margin-bottom: 6px; line-height: 1.5;">{point}</li>')
                    else:
                        break
                    i += 1
                html_parts.append('</ul></div>')
                continue
            
            # WHY IT MATTERS section
            elif line.startswith('WHY IT MATTERS:'):
                content_parts = [line.replace('WHY IT MATTERS:', '').strip()]
                i += 1
                # Collect content until next section or empty line
                while i < len(lines):
                    next_line = lines[i].strip()
                    if next_line.startswith(('KEY POINTS:', 'OVERVIEW:', 'SIMPLE EXPLANATION:')):
                        break
                    if not next_line and content_parts:
                        break
                    if next_line:
                        content_parts.append(next_line)
                    i += 1
                content = ' '.join(content_parts).strip()
                if content:
                    html_parts.append(f'<div style="margin-bottom: 12px;"><strong style="color: #1e3a8a;">Why It Matters:</strong> {content}</div>')
                continue
            
            # SIMPLE EXPLANATION section
            elif line.startswith('SIMPLE EXPLANATION:'):
                content_parts = [line.replace('SIMPLE EXPLANATION:', '').strip()]
                i += 1
                # Collect content until next section or empty line
                while i < len(lines):
                    next_line = lines[i].strip()
                    if next_line.startswith(('KEY POINTS:', 'WHY IT MATTERS:', 'OVERVIEW:')):
                        break
                    if not next_line and content_parts:
                        break
                    if next_line:
                        content_parts.append(next_line)
                    i += 1
                content = ' '.join(content_parts).strip()
                if content:
                    html_parts.append(f'<div style="margin-bottom: 12px;"><strong style="color: #1e3a8a;">Simple Explanation:</strong> {content}</div>')
                continue
            
            i += 1
        
        # If no structured format found, return as-is with line breaks preserved
        if not html_parts:
            formatted = summary_text.replace('\n', '<br>')
            return f'<div>{formatted}</div>'
        
        return ''.join(html_parts)

    def aggregate_today_news(self) -> List[dict]:
        """
        Aggregate all news articles from today and format them for email.
        
        Returns:
            List of dictionaries in the format:
            {
                "category": str,  # Same as source
                "title": str,
                "summary": str,
                "source": str,
                "link": str
            }
        """
        session = self.get_session()
        
        try:
            # Get today's date (start of day)
            today_start = datetime.combine(date.today(), datetime.min.time())
            today_end = datetime.combine(date.today(), datetime.max.time())
            
            # Query articles created today
            articles = session.query(Article).filter(
                Article.created_at >= today_start,
                Article.created_at <= today_end
            ).order_by(Article.created_at.desc()).all()
            
            # Convert to news_items format
            news_items = []
            for article in articles:
                # Only include articles that have summaries
                if not article.summary:
                    continue
                    
                news_item = {
                    "category": article.source,  # Use source as category
                    "title": article.title,
                    "summary": self._format_summary_html(article.summary),  # Format as HTML
                    "source": article.source,
                    "link": article.link
                }
                news_items.append(news_item)
            
            return news_items
            
        finally:
            session.close()

