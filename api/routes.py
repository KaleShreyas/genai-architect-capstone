"""Submission / A2A endpoints"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from api.schemas import Product, SubmissionPayload
from db.crud import insert_draft_submission, get_product_by_sku, search_catalog, get_recommendations
from utils.preprocess import preprocess_submission
from utils.storage import stage_to_blob, archive_to_cosmos

import csv
import io
import logging

router = APIRouter()

# ----- PHASE 1: Seller Submission -----

@router.post("/sku/submit")
async def submit_sku(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    decoded = content.decode("utf-8")
    csv_reader = csv.DictReader(io.StringIO(decoded))

    submissions = []
    for row in csv_reader:
        cleaned = preprocess_submission(row)  # HTML sanitization, metadata
        submissions.append(cleaned)

        # Insert into DB as draft
        insert_draft_submission(cleaned)

        # Save to blob
        stage_to_blob(row["sku"], row)

        # Optional archive
        try:
            archive_to_cosmos(row)
        except Exception as e:
            logging.warning(f"Cosmos archiving failed: {e}")

    return {"message": f"{len(submissions)} SKUs submitted successfully."}


# ----- PHASE 5: A2A Catalog Endpoints -----

@router.get("/catalog/{sku}", response_model=Product)
def get_product(sku: str):
    product = get_product_by_sku(sku)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/catalog/search", response_model=list[Product])
def search(query: str = Query(...)):
    return search_catalog(query)

@router.get("/catalog/recommendations", response_model=list[Product])
def recommend(
    category: str = Query(None),
    price_min: float = Query(None),
    price_max: float = Query(None)
):
    return get_recommendations(category, price_min, price_max)
