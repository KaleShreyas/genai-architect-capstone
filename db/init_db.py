"""Bootstrap script to create schema"""

from sqlalchemy import create_engine
from db.models import Base

# For SQLite
DATABASE_URL = "sqlite:///./data/catalog.db"

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
