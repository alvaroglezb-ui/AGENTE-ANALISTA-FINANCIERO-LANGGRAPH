import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()


def get_database_url() -> str:
    """
    Get database URL from environment variables or use SQLite as fallback.
    
    Returns:
        Database URL string
    """
    # Check if PostgreSQL environment variables are set
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB")
    
    # If all PostgreSQL vars are set, use PostgreSQL
    if all([user, password, host, database]):
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    # Otherwise, use SQLite as default
    return "sqlite:///rss_articles.db"


def create_engine_instance(database_url: str = None):
    """
    Create SQLAlchemy engine instance.
    
    Args:
        database_url: Optional database URL. If not provided, uses get_database_url()
        
    Returns:
        SQLAlchemy engine
    """
    if database_url is None:
        database_url = get_database_url()
    
    try:
        return create_engine(database_url, echo=False)
    except Exception as e:
        if "psycopg2" in str(e) or "psycopg" in str(e):
            raise ImportError(
                "PostgreSQL driver not found. Install with: pip install psycopg2-binary\n"
                "Or ensure PostgreSQL environment variables are not set to use SQLite."
            ) from e
        raise


# Create engine and session factory
engine = create_engine_instance()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Session:
    """
    Get a new database session.
    
    Returns:
        SQLAlchemy session
    """
    return SessionLocal()


def get_engine():
    """
    Get the database engine instance.
    
    Returns:
        SQLAlchemy engine
    """
    return engine