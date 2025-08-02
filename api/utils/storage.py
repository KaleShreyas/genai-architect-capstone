"""Wraps all Azure I/O operations"""

import os
from azure.storage.blob import BlobServiceClient
from azure.cosmos import CosmosClient
import json

# Blob setup
blob_service_client = BlobServiceClient.from_connection_string(os.getenv("BLOB_CONN_STRING"))
container_name = os.getenv("BLOB_CONTAINER", "submissions")

def stage_to_blob(sku, data):
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=f"{sku}.json")
    blob_client.upload_blob(json.dumps(data), overwrite=True)

# Cosmos DB setup (optional)
cosmos_client = CosmosClient(os.getenv("COSMOS_URI"), credential=os.getenv("COSMOS_KEY"))
db = cosmos_client.get_database_client(os.getenv("COSMOS_DB", "vendorArchive"))
container = db.get_container_client(os.getenv("COSMOS_CONTAINER", "rawSubmissions"))

def archive_to_cosmos(data):
    container.upsert_item(data)
