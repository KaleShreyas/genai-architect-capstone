"""
HTML sanitization (with bleach) to clean seller-submitted descriptions
Language detection using langdetect to enrich metadata
"""

import bleach
from langdetect import detect

def preprocess_submission(row):
    sanitized_description = bleach.clean(row["description"], strip=True)
    language = detect(sanitized_description)

    return {
        "sku": row["sku"],
        "title": row["title"].strip(),
        "description": sanitized_description,
        "category": row["category"],
        "brand": row["brand"],
        "language": language,
        "status": "draft"
    }
