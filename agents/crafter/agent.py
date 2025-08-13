"""LangGraph logic for content generation"""

import os
import json
from typing import Dict, Any

from openai import OpenAI
from langfuse import Langfuse

from agents.crafter.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from agents.crafter.image_gen import generate_hero_image_url
from utils.storage import upload_submission_file  # uses azure-storage-blob (modern SDK)
from db.crud import update_crafter_outputs  # you'll add this helper at the end

# --- Azure OpenAI setup (text) ---
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")   # https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
TEXT_MODEL = os.getenv("TEXT_MODEL", "gpt-4o-mini")

client = OpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    base_url=f"{AZURE_OPENAI_ENDPOINT}/openai",
)

# --- LangFuse ---
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

# --- Blob containers for artifacts ---
CONTENT_CONTAINER = os.getenv("CONTENT_CONTAINER", "processed-content")
IMAGES_CONTAINER = os.getenv("IMAGES_CONTAINER", "hero-images")

def _build_user_payload(state: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "sku": state.get("sku") or state.get("listing_id"),
        "title": state.get("title", ""),
        "description": state.get("description", ""),
        "category": state.get("category", ""),
        "brand": state.get("brand", ""),
        "language": state.get("language", ""),
    }
    return payload

def _llm_structured_copy(vendor_payload: Dict[str, Any], trace):
    user_prompt = USER_PROMPT_TEMPLATE.format(**vendor_payload)

    span = trace.span(name="crafter-gpt")
    try:
        # Use Responses API for JSON-friendly outputs
        resp = client.responses.create(
            model=TEXT_MODEL,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_output_tokens=800,
            response_format={"type": "json_object"}
        )
        raw = resp.output_text  # already a JSON string per response_format
        data = json.loads(raw)
        span.end(output=data, status="success")
        return data
    except Exception as e:
        span.end(output=str(e), status="error")
        raise

def _persist_artifacts(sku: str, crafter_json: dict, image_url: str):
    """
    Persist two artifacts to Blob:
    1) JSON with crafter outputs
    2) A small JSON 'pointer' to hero image URL (so capstone can dereference)
    """
    # 1) Store crafted content JSON
    content_blob_name = f"{sku}_crafter.json"
    upload_submission_file(
        file_bytes=json.dumps(crafter_json, ensure_ascii=False),
        filename=content_blob_name,
        content_type="application/json"
    )

    # 2) Store image pointer JSON (we are not downloading the image; just keep URL)
    image_pointer = {"sku": sku, "hero_image_url": image_url}
    image_blob_name = f"{sku}_image_pointer.json"
    upload_submission_file(
        file_bytes=json.dumps(image_pointer, ensure_ascii=False),
        filename=image_blob_name,
        content_type="application/json"
    )

def run_crafter(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node.
    Input state (minimum):
      - listing_id or sku
      - title, description, category, brand, language (from vendor)
    Output enriches state with:
      - seo_title, seo_description, attributes (dict)
      - hero_image_url
      - content_blob_paths (optional)
    Also updates DB row for this SKU.
    """
    sku = state.get("sku") or state.get("listing_id")
    if not sku:
        raise ValueError("Crafter: missing 'sku' or 'listing_id' in state.")

    trace = langfuse.trace(name=f"crafter-{sku}", tags=["crafter", "content"], input=state)

    # 1) Build vendor payload from state
    vendor_payload = _build_user_payload(state)

    # 2) Generate structured copy via GPT-4o mini
    result = _llm_structured_copy(vendor_payload, trace)
    seo_title = result.get("seo_title", "").strip()
    seo_description = result.get("seo_description", "").strip()
    attributes = result.get("attributes", {}) or {}

    # 3) Generate hero image (URL)
    hero_image_url = generate_hero_image_url(sku, seo_title or vendor_payload["title"], {**attributes, "category": vendor_payload.get("category")})

    # 4) Persist artifacts to Blob
    crafter_json = {
        "sku": sku,
        "seo_title": seo_title,
        "seo_description": seo_description,
        "attributes": attributes,
        "hero_image_url": hero_image_url
    }
    _persist_artifacts(sku, crafter_json, hero_image_url)

    # 5) Update same SQLite/Postgres row
    update_crafter_outputs(
        sku=sku,
        seo_title=seo_title,
        seo_description=seo_description,
        attributes_json=json.dumps(attributes, ensure_ascii=False),
        hero_image_url=hero_image_url
    )

    trace.end(output=crafter_json, status="success")

    # 6) Return enriched state for next agent (Inspector)
    return {
        **state,
        "seo_title": seo_title,
        "seo_description": seo_description,
        "attributes": attributes,
        "hero_image_url": hero_image_url,
        "crafter_done": True
    }
