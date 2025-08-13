"""Local DB I/O operations"""

import sqlite3
from typing import List, Optional, Dict

DB_PATH = "data/catalog.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def insert_draft_submission(data: Dict):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO catalog (sku, title, description, category, price, status)
            VALUES (?, ?, ?, ?, ?, 'draft')
        """, (
            data["sku"],
            data["title"],
            data["description"],
            data.get("category", ""),
            data.get("price", 0.0),
        ))
        conn.commit()

def get_product_by_sku(sku: str) -> Optional[Dict]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM catalog WHERE sku = ? AND status = 'approved'
        """, (sku,))
        row = cursor.fetchone()
        return dict(row) if row else None

def search_catalog(query: str) -> List[Dict]:
    pattern = f"%{query}%"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM catalog
            WHERE status = 'approved' AND (title LIKE ? OR description LIKE ?)
        """, (pattern, pattern))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_recommendations(category: Optional[str] = None, price_min: Optional[float] = None, price_max: Optional[float] = None) -> List[Dict]:
    query = "SELECT * FROM catalog WHERE status = 'approved'"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)
    if price_min is not None:
        query += " AND price >= ?"
        params.append(price_min)
    if price_max is not None:
        query += " AND price <= ?"
        params.append(price_max)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def update_crafter_outputs(sku: str, seo_title: str, seo_description: str, attributes_json: str, hero_image_url: str):
    """
    Updates the existing catalog row for this SKU with the crafter outputs.
    Keeps status as-is (draft) so the Inspector can evaluate next.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Ensure columns exist; if not, add them to your schema:
        # ALTER TABLE catalog ADD COLUMN seo_title TEXT;
        # ALTER TABLE catalog ADD COLUMN seo_description TEXT;
        # ALTER TABLE catalog ADD COLUMN attributes_json TEXT;
        # ALTER TABLE catalog ADD COLUMN image_url TEXT;

        cursor.execute("""
            UPDATE catalog
            SET seo_title = ?, seo_description = ?, attributes_json = ?, image_url = ?
            WHERE sku = ?
        """, (seo_title, seo_description, attributes_json, hero_image_url, sku))
        conn.commit()
