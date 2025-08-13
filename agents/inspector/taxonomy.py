"""Google Retail Taxonomy logic"""

import os
from typing import Optional, Tuple

# Optional Azure AI Search
try:
    from azure.search.documents import SearchClient
    from azure.core.credentials import AzureKeyCredential
    _HAS_AZURE_SEARCH = True
except Exception:
    _HAS_AZURE_SEARCH = False

# Optional Weaviate
try:
    import weaviate
    _HAS_WEAVIATE = True
except Exception:
    _HAS_WEAVIATE = False


def azure_search_similarity(query: str) -> Tuple[Optional[str], float]:
    """
    Searches a 'google-retail-taxonomy' index with fields 'path' (full path) and 'name'.
    Returns (best_category_path, score in 0..1).
    """
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    key = os.getenv("AZURE_SEARCH_KEY")
    index = os.getenv("AZURE_SEARCH_INDEX", "google-retail-taxonomy")

    if not (_HAS_AZURE_SEARCH and endpoint and key):
        return None, 0.0

    client = SearchClient(endpoint=endpoint, index_name=index, credential=AzureKeyCredential(key))
    results = client.search(search_text=query, top=1)
    best = None
    best_score = 0.0
    for doc in results:
        # Azure Search returns @search.score typically ~ 0..1-ish
        best = doc.get("path") or doc.get("name")
        best_score = float(getattr(doc, "@search.score", 0.0))
        break
    return best, best_score


def weaviate_similarity(query: str) -> Tuple[Optional[str], float]:
    """
    Searches a Weaviate collection 'RetailTaxonomy' with a 'path' property.
    Returns (best_category_path, pseudo_score 0..1).
    """
    if not _HAS_WEAVIATE:
        return None, 0.0

    url = os.getenv("WEAVIATE_URL")
    api_key = os.getenv("WEAVIATE_API_KEY")
    if not url:
        return None, 0.0

    client = weaviate.Client(url=url, additional_headers={"X-OpenAI-Api-Key": api_key} if api_key else {})
    try:
        res = client.query.get("RetailTaxonomy", ["path"]).with_near_text({"concepts": [query]}).with_limit(1).do()
        items = res.get("data", {}).get("Get", {}).get("RetailTaxonomy", [])
        if not items:
            return None, 0.0
        best = items[0].get("path")
        # No canonical score; assume strong match
        return best, 0.85
    except Exception:
        return None, 0.0


def align_category(candidate: str) -> Tuple[Optional[str], float, str]:
    """
    Try Azure Search first, then Weaviate. Returns (aligned_path, score, backend).
    """
    if candidate is None:
        candidate = ""
    best, score = azure_search_similarity(candidate)
    if best:
        return best, score, "azure_search"
    best, score = weaviate_similarity(candidate)
    if best:
        return best, score, "weaviate"
    return None, 0.0, "none"
