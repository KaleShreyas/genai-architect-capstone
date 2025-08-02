# genai-architect-capstone
Retail Marketplace Agent System

# 📁 genai-multiagent-pipeline
## Agents
- `agents/`
  - `crafter/`
    - `__init__.py`
    - `agent.py` — LangGraph logic for content generation
    - `prompts.py` — Prompt templates
    - `image_gen.py` — Calls DALL·E or SD-XL
  - `inspector/`
    - `__init__.py`
    - `agent.py` — Rule checks and scoring
    - `taxonomy.py` — Google Retail Taxonomy logic
    - `rules_loader.py` — Load compliance rules
  - `answer_agent/`
    - `__init__.py`
    - `agent.py` — A2A response logic
    - `formatter.py` — Converts catalog rows to text/JSON

## Orchestrator
- `orchestrator/`
  - `__init__.py`
  - `flow.py` — LangGraph workflow
  - `router.py` — Routing and error handling
  - `service_bus.py` — Human-review queue logic

## API Layer
- `api/`
  - `app.py` — FastAPI entrypoint
  - `routes.py` — Submission and catalog APIs
  - `schemas.py` — Pydantic models
  - `openapi/openapi.yaml` — A2A OpenAPI 3.1 spec

- `utils/`
  - `__init__.py`
  - `preprocess.py` — Submission pre-processing
  - `storage.py` — Azure I/O operations

## Database Layer
- `db/`
  - `models.py` — ORM schema for catalog/status
  - `crud.py` — DB interactions
  - `init_db.py` — Setup script

## Infrastructure & Deployment
- `infra/`
  - `Dockerfile.agent` — Base Dockerfile for agents
  - `Dockerfile.api`
  - `docker-compose.yml` — For local testing
  - `deploy.sh` — Push to Azure Container Registry
  - `bicep/` or `terraform/`
    - `main.bicep` or `main.tf`
    - `params.json` or `variables.tf`

## Monitoring & Observability
- `monitor/`
  - `langfuse_config.yaml`
  - `azure_monitor_config.json`
  - `grafana_dashboards/catalog_ops.json`

## Static Assets & Rules
- `submission_samples/vendor_submission_api_sample.csv`
- `compliance_rules/compliance_rules.txt`

## GitHub Actions (CI/CD)
- `.github/workflows/ci-cd.yml`

## Root Files
- `.env` — Local environment config
- `.gitignore`
- `README.md`
- `requirements.txt`