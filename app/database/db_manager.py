from typing import Optional
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
                            collection_id=collection.id
                        )
                        session.add(article)

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

