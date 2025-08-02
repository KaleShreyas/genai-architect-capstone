# genai-architect-capstone
Retail Marketplace Agent System

## Project structure
genai-multiagent-pipeline/
│
├── agents/
│   ├── crafter/
│   │   ├── __init__.py
│   │   ├── agent.py              # LangGraph node logic
│   │   ├── prompts.py            # GPT prompt templates
│   │   ├── image_gen.py          # DALL·E / SD-XL calls
│   │   └── tests/
│   │       └── test_agent.py
│   │
│   ├── inspector/
│   │   ├── __init__.py
│   │   ├── agent.py              # Compliance rule engine
│   │   ├── taxonomy.py           # Azure AI Search calls
│   │   ├── rules_loader.py       # Parse compliance_rules.txt
│   │   └── tests/
│   │       └── test_agent.py
│   │
│   └── answer_agent/
│       ├── __init__.py
│       ├── agent.py              # A2A OpenAPI-compatible logic
│       ├── formatter.py          # Text & JSON generation
│       └── tests/
│           └── test_agent.py
│
├── orchestrator/
│   ├── __init__.py
│   ├── flow.py                   # LangGraph workflow definition
│   ├── router.py                 # Handles routing & retries
│   ├── service_bus.py            # For edge-case queues
│   └── tests/
│       └── test_flow.py
│
├── api/
│   ├── app.py                    # FastAPI entrypoint
│   ├── routes.py                 # Submission / A2A endpoints
│   ├── schemas.py                # Pydantic request/response schemas
│   └── openapi/                  
│       └── openapi.yaml          # A2A spec (OpenAPI 3.1)
│
├── db/
│   ├── models.py                 # SQLite/Postgres ORM models
│   ├── crud.py                   # Read/write methods
│   ├── init_db.py                # Bootstrap script
│   └── migrations/               # Alembic migrations (if PostgreSQL)
│
├── infra/
│   ├── Dockerfile.agent          # Shared base for agents
│   ├── Dockerfile.api
│   ├── docker-compose.yml        # For local multi-service dev
│   ├── deploy.sh                 # Push to ACR
│   └── bicep/                    # Azure infra-as-code (or Terraform)
│       ├── main.bicep
│       └── params.json
│
├── monitor/
│   ├── langfuse_config.yaml      # Prompt tracing
│   ├── azure_monitor_config.json
│   └── grafana_dashboards/
│       └── catalog_ops.json
│
├── submission_samples/
│   └── vendor_submission_api_sample.csv
│
├── compliance_rules/
│   └── compliance_rules.txt
│
├── .github/
│   └── workflows/
│       └── ci-cd.yml             # GitHub Actions pipeline
│
├── .env                         # Secrets (loaded in dev only)
├── .gitignore
├── README.md
├── requirements.txt             # Python deps
└── pyproject.toml               # (Optional) for poetry/pipenv
