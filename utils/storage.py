"""Wraps all Azure I/O operations"""

from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.cosmos import CosmosClient, PartitionKey

import os
from typing import Union
import uuid

# Blob setup
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = "vendor-submissions"

blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

# Ensure container exists
def ensure_container():
    try:
        container_client.create_container()
    except Exception:
        pass  # Already exists

def stage_to_blob(file_bytes: Union[bytes, str], filename: str, content_type: str = "application/json") -> str:
    """
    Uploads a submission file (CSV or JSON) to Azure Blob Storage and returns the blob URL.
    """
    ensure_container()

    if isinstance(file_bytes, str):
        file_bytes = file_bytes.encode("utf-8")

    blob_name = f"{uuid.uuid4()}_{filename}"
    blob_client = container_client.get_blob_client(blob_name)

    blob_client.upload_blob(
        file_bytes,
        overwrite=True,
        content_settings=ContentSettings(content_type=content_type)
    )

    return blob_client.url

def download_blob_as_text(blob_name: str) -> str:
    """
    Downloads a blob and returns its contents as a string.
    """
    blob_client = container_client.get_blob_client(blob_name)
    blob_data = blob_client.download_blob()
    return blob_data.readall().decode("utf-8")

# Cosmos DB setup (optional)
COSMOS_URI = os.getenv("COSMOS_URI")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DB = os.getenv("COSMOS_DB", "vendorArchive")
COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER", "rawSubmissions")

cosmos_client = CosmosClient(COSMOS_URI, credential=COSMOS_KEY)

# Create/get database and container references
db = cosmos_client.create_database_if_not_exists(id=COSMOS_DB)
container = db.create_container_if_not_exists(
    id=COSMOS_CONTAINER,
    partition_key=PartitionKey(path="/sku"),  # adjust to your data structure
    offer_throughput=400
)

def archive_to_cosmos(data: dict):
    """
    Archives raw submission data to Cosmos DB. Assumes `data` contains a unique `sku`.
    """
    try:
        container.upsert_item(data)
    except Exception as e:
        print(f"[Cosmos] Failed to archive submission: {e}")
