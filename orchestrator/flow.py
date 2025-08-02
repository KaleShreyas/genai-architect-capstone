"""LangGraph workflow"""

from langgraph.graph import StateGraph
from orchestrator.router import handle_result, route_error
from agents.crafter.agent import run_crafter
from agents.inspector.agent import run_inspector
from db.crud import update_status
from langfuse import Langfuse
import os

MAX_RETRIES = 2

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

def trace_with_langfuse(node_name):
    def wrapper(state):
        listing_id = state.get("listing_id", "unknown")
        trace = langfuse.trace(name=f"{node_name}-{listing_id}", tags=["orchestrator"])
        try:
            trace.span(name="start")
            updated_state = globals()[f"run_{node_name.lower()}"](state)
            trace.span(name="complete", status="success")
            trace.end()
            return updated_state
        except Exception as e:
            trace.span(name="error", status="error", input=state, output=str(e))
            trace.end()
            raise e
    return wrapper

def build_workflow():
    graph = StateGraph(state_type=dict)

    graph.add_node("Crafter", trace_with_langfuse("Crafter"))
    graph.add_node("Inspector", trace_with_langfuse("Inspector"))
    graph.add_node("Decision", handle_result)

    # Entry and normal flow
    graph.set_entry_point("Crafter")
    graph.add_edge("Crafter", "Inspector")
    graph.add_edge("Inspector", "Decision")

    # Retry logic via LangGraph edges (if `retry_count` < MAX_RETRIES)
    def retry_decider(state):
        count = state.get("retry_count", 0)
        return "retry" if count < MAX_RETRIES else "fail"

    graph.add_node("retry", lambda state: {
        **state,
        "retry_count": state.get("retry_count", 0) + 1
    })

    graph.add_conditional_edge("Inspector", retry_decider, {
        "retry": "Crafter",     # retry entire flow
        "fail": "Decision"      # end with fail
    })

    # Handle uncaught exceptions (network, auth, etc.)
    graph.add_error_handler("*", route_error)

    return graph.compile()

# Dev script for test
# if __name__ == "__main__":
#     flow = build_workflow()

#     test_state = {
#         "listing_id": "sku1234",
#         "raw_payload": {
#             "title": "Green T-Shirt",
#             "description": "Cotton, 100% eco",
#             "category": "Apparel > Tops"
#         },
#         "retry_count": 0
#     }

#     output = flow.invoke(test_state)
#     print("Final State:", output)
