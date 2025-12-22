from typing import Optional, List
from datetime import datetime, date
from sqlalchemy import text
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
        Automatically detects language from summary headers.
        
        Args:
            summary_text: Plain text summary with structure (English or Spanish)
        
        Returns:
            Formatted HTML string
        """
        # Import here to avoid circular import
        from app.agent.language_config import get_language_config, LANGUAGE_CONFIG
        
        if not summary_text:
            return ""
        
        # Detect language from first header found
        detected_lang = None
        for line in summary_text.split('\n'):
            line_stripped = line.strip()
            if line_stripped.startswith('RESUMEN:') or line_stripped.startswith('PUNTOS CLAVE:'):
                detected_lang = "ES"
                break
            elif line_stripped.startswith('OVERVIEW:') or line_stripped.startswith('KEY POINTS:'):
                detected_lang = "ENG"
                break
        
        # Use detected language or fall back to current setting
        if detected_lang:
            from app.agent.language_config import LANGUAGE_CONFIG
            lang_config = LANGUAGE_CONFIG[detected_lang]
        else:
            lang_config = get_language_config()
        
        html_parts = []
        lines = summary_text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # OVERVIEW/RESUMEN section
            overview_header = lang_config["headers"]["overview"] + ":"
            if line.startswith(overview_header) or line.startswith("OVERVIEW:") or line.startswith("RESUMEN:"):
                header_text = lang_config["display_headers"]["overview"]
                # Remove any of the possible headers
                content_parts = [line.replace(overview_header, '').replace("OVERVIEW:", '').replace("RESUMEN:", '').strip()]
                next_sections = (
                    lang_config["headers"]["key_points"] + ":",
                    lang_config["headers"]["why_it_matters"] + ":",
                    lang_config["headers"]["simple_explanation"] + ":",
                    "KEY POINTS:", "PUNTOS CLAVE:",
                    "WHY IT MATTERS:", "POR QUÉ IMPORTA:",
                    "SIMPLE EXPLANATION:", "EXPLICACIÓN SIMPLE:"
                )
                
                i += 1
                # Collect content until next section or empty line
                while i < len(lines):
                    next_line = lines[i].strip()
                    if next_line.startswith(next_sections):
                        break
                    if not next_line and content_parts:
                        break
                    if next_line:
                        content_parts.append(next_line)
                    i += 1
                content = ' '.join(content_parts).strip()
                if content:
                    html_parts.append(f'<div style="margin-bottom: 12px;"><strong style="color: #1e3a8a;">{header_text}</strong> {content}</div>')
                continue
            
            # KEY POINTS/PUNTOS CLAVE section
            key_points_header = lang_config["headers"]["key_points"] + ":"
            if line.startswith(key_points_header) or line.startswith("KEY POINTS:") or line.startswith("PUNTOS CLAVE:"):
                header_text = lang_config["display_headers"]["key_points"]
                next_sections = (
                    lang_config["headers"]["why_it_matters"] + ":",
                    lang_config["headers"]["simple_explanation"] + ":",
                    lang_config["headers"]["overview"] + ":",
                    "WHY IT MATTERS:", "POR QUÉ IMPORTA:",
                    "SIMPLE EXPLANATION:", "EXPLICACIÓN SIMPLE:",
                    "OVERVIEW:", "RESUMEN:"
                )
                
                html_parts.append(f'<div style="margin-bottom: 12px;"><strong style="color: #1e3a8a;">{header_text}</strong><ul style="margin: 8px 0; padding-left: 20px;">')
                i += 1
                # Collect bullet points
                while i < len(lines):
                    bullet_line = lines[i].strip()
                    if bullet_line.startswith('•') or bullet_line.startswith('-'):
                        # Remove bullet characters from anywhere in the string
                        point = bullet_line.replace('•', '').replace('-', '').strip()
                        if point:
                            html_parts.append(f'<li style="margin-bottom: 6px; line-height: 1.5;">{point}</li>')
                    elif bullet_line and not bullet_line.startswith(next_sections):
                        # Handle points without bullet prefix - still remove any bullet chars
                        point = bullet_line.replace('•', '').replace('-', '').strip()
                        if point:
                            html_parts.append(f'<li style="margin-bottom: 6px; line-height: 1.5;">{point}</li>')
                    else:
                        break
                    i += 1
                html_parts.append('</ul></div>')
                continue
            
            # WHY IT MATTERS/POR QUÉ IMPORTA section
            why_matters_header = lang_config["headers"]["why_it_matters"] + ":"
            if line.startswith(why_matters_header) or line.startswith("WHY IT MATTERS:") or line.startswith("POR QUÉ IMPORTA:"):
                header_text = lang_config["display_headers"]["why_it_matters"]
                # Remove any of the possible headers
                content_parts = [line.replace(why_matters_header, '').replace("WHY IT MATTERS:", '').replace("POR QUÉ IMPORTA:", '').strip()]
                next_sections = (
                    lang_config["headers"]["key_points"] + ":",
                    lang_config["headers"]["simple_explanation"] + ":",
                    lang_config["headers"]["overview"] + ":",
                    "KEY POINTS:", "PUNTOS CLAVE:",
                    "SIMPLE EXPLANATION:", "EXPLICACIÓN SIMPLE:",
                    "OVERVIEW:", "RESUMEN:"
                )
                
                i += 1
                # Collect content until next section or empty line
                while i < len(lines):
                    next_line = lines[i].strip()
                    if next_line.startswith(next_sections):
                        break
                    if not next_line and content_parts:
                        break
                    if next_line:
                        content_parts.append(next_line)
                    i += 1
                content = ' '.join(content_parts).strip()
                if content:
                    html_parts.append(f'<div style="margin-bottom: 12px;"><strong style="color: #1e3a8a;">{header_text}</strong> {content}</div>')
                continue
            
            # SIMPLE EXPLANATION/EXPLICACIÓN SIMPLE section
            simple_explanation_header = lang_config["headers"]["simple_explanation"] + ":"
            if line.startswith(simple_explanation_header) or line.startswith("SIMPLE EXPLANATION:") or line.startswith("EXPLICACIÓN SIMPLE:"):
                header_text = lang_config["display_headers"]["simple_explanation"]
                # Remove any of the possible headers
                content_parts = [line.replace(simple_explanation_header, '').replace("SIMPLE EXPLANATION:", '').replace("EXPLICACIÓN SIMPLE:", '').strip()]
                next_sections = (
                    lang_config["headers"]["key_points"] + ":",
                    lang_config["headers"]["why_it_matters"] + ":",
                    lang_config["headers"]["overview"] + ":",
                    "KEY POINTS:", "PUNTOS CLAVE:",
                    "WHY IT MATTERS:", "POR QUÉ IMPORTA:",
                    "OVERVIEW:", "RESUMEN:"
                )
                
                i += 1
                # Collect content until next section or empty line
                while i < len(lines):
                    next_line = lines[i].strip()
                    if next_line.startswith(next_sections):
                        break
                    if not next_line and content_parts:
                        break
                    if next_line:
                        content_parts.append(next_line)
                    i += 1
                content = ' '.join(content_parts).strip()
                if content:
                    html_parts.append(f'<div style="margin-bottom: 12px;"><strong style="color: #1e3a8a;">{header_text}</strong> {content}</div>')
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

    def get_all_emails(self) -> List[str]:
        """
        Retrieve all email addresses from the emails table.
        
        Returns:
            List of email addresses (strings)
        """
        session = self.get_session()
        try:
            # Query the emails table directly using raw SQL
            result = session.execute(text("SELECT email FROM emails"))
            emails = [row[0] for row in result.fetchall()]
            return emails
        except Exception as e:
            print(f"✗ Error retrieving emails: {e}")
            return []
        finally:
            session.close()

