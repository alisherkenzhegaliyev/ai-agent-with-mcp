# src/database/migrations.py
import json
from src.data.db import engine, Base, Product, SessionLocal


def migrate_json_to_sqlite():
    """Migrate existing products.json to SQLite"""
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Load existing JSON data
    with open("src/data/products.json") as f:
        products = json.load(f)

    # Insert into SQLite
    db = SessionLocal()
    for prod in products:
        db.add(Product(**prod))
    db.commit()
    db.close()


if __name__ == "__main__":
    migrate_json_to_sqlite()
