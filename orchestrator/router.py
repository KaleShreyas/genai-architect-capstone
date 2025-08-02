"""Handles routing & retries"""

from azure.servicebus import ServiceBusClient, ServiceBusMessage
from db.crud import update_status
import os
import logging
from langfuse import Langfuse

SERVICE_BUS_CONN_STR = os.getenv("SERVICE_BUS_CONN_STR")
QUEUE_NAME = "review-queue"
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

def handle_result(state):
    listing_id = state.get("listing_id")
    score = state.get("compliance_score", 0)

    status = (
        "approved" if score >= 80 else
        "needs_fix" if score >= 50 else
        "rejected"
    )

    update_status(listing_id, status)
    return {**state, "final_status": status}

def route_error(state, error):
    listing_id = state.get("listing_id", "unknown")
    reason = str(error)

    logging.error(f"[Router] Error on listing {listing_id}: {reason}")

    trace = langfuse.trace(name=f"error-{listing_id}", tags=["orchestrator"])
    trace.span(name="exception", input=state, output=reason, status="error")
    trace.end()

    try:
        servicebus_client = ServiceBusClient.from_connection_string(SERVICE_BUS_CONN_STR)
        with servicebus_client:
            sender = servicebus_client.get_queue_sender(queue_name=QUEUE_NAME)
            with sender:
                msg = ServiceBusMessage(str(state))
                sender.send_messages(msg)
    except Exception as e:
        logging.critical(f"Failed to route error to Service Bus: {e}")
