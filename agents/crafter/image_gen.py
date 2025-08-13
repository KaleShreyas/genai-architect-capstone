"""Calls DALL·E or SD-XL"""

import os
import json
from typing import Optional

# Prefer Azure OpenAI Images (DALL·E 3). If not available, return a dummy URL.
# Using the unified OpenAI client that supports Azure endpoints.
from openai import OpenAI

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")   # e.g., https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
DALLE_MODEL = os.getenv("DALLE_MODEL", "dall-e-3")

client = OpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    base_url=f"{AZURE_OPENAI_ENDPOINT}/openai",
)

def build_image_prompt(sku: str, title: str, attrs: dict) -> str:
    # Keep it safe & generic—policy-safe hero image brief
    parts = [f"High quality studio hero image for product: {title}."]
    if color := attrs.get("color"):
        parts.append(f"Primary color: {color}.")
    if material := attrs.get("material"):
        parts.append(f"Material: {material}.")
    if attrs.get("category"):
        parts.append(f"Category: {attrs['category']}.")
    parts.append("On a clean, neutral background, well-lit, crisp details.")
    return " ".join(parts)

def generate_hero_image_url(sku: str, title: str, attrs: dict) -> str:
    """
    Calls Azure OpenAI Images (DALL·E 3). If not enabled, returns a deterministic dummy URL.
    """
    try:
        prompt = build_image_prompt(sku, title, attrs)
        resp = client.images.generate(
            model=DALLE_MODEL,
            prompt=prompt,
            size="1024x1024",
            n=1
        )
        # Azure returns a base64 or URL depending on configuration; prefer URL if present.
        if resp.data and resp.data[0].url:
            return resp.data[0].url
        # If only b64 is returned, you could decode & upload to Blob. For capstone, return a placeholder:
        return f"https://dummy.example/hero/{sku}.png"
    except Exception:
        # Fallback for environments without image generation enabled
        return f"https://dummy.example/hero/{sku}.png"
