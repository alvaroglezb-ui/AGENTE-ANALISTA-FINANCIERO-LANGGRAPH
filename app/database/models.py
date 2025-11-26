from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()


class Article(Base):
    """SQLAlchemy model for Article."""
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    source = Column(String(200), nullable=False)
    link = Column(String(1000), nullable=False, unique=True)
    published = Column(String(200))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign key to collection
    collection_id = Column(Integer, ForeignKey('collections.id'), nullable=False)
    
    # Relationship
    collection = relationship("Collection", back_populates="articles")


class Collection(Base):
    """SQLAlchemy model for collection (grouped articles by source)."""
    __tablename__ = 'collections'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(200), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key to extraction (optional - collections can exist without extraction)
    extraction_id = Column(Integer, ForeignKey('extractions.id'), nullable=True)
    
    # Relationships
    articles = relationship("Article", back_populates="collection", cascade="all, delete-orphan")
    extraction = relationship("Extraction", back_populates="collections")


class Extraction(Base):
    """SQLAlchemy model for extraction (container for scraping results)."""
    __tablename__ = 'extractions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to collections
    collections = relationship("Collection", back_populates="extraction")

