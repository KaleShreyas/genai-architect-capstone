"""
SQLite ORM models using SQLAlchemy

CREATE TABLE catalog (
    sku TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    category TEXT,
    price REAL,
    status TEXT
);
"""

from sqlalchemy import Column, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CatalogItem(Base):
    __tablename__ = 'catalog'

    sku = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    price = Column(Float, default=0.0)
    status = Column(String, default='draft')  # 'draft', 'approved', etc.
