"""Pydantic request/response schemas"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Literal

# Submission schema based on vendor_submission_api_sample.csv
class SubmissionPayload(BaseModel):
    sku: str
    title: str
    description: str
    category: str
    brand: str
    language: str | None = None

# A2A catalog response
class Product(BaseModel):
    sku: str
    title: str
    description: str
    category: str
    price: float
    currency: str = "INR"
    availability: Literal["in_stock", "out_of_stock", "limited"]
    image_url: HttpUrl
