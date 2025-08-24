# AI Text‑to‑SQL Chatbot (LLM + Guardrails + Semantic Layer + Monitoring)

**What you asked for**: End‑to‑end code for an AI Text‑to‑SQL chatbot that uses LLM function‑calling, blocks unsafe queries with guardrails & verification, supports multiple relational databases, includes a semantic KPI layer, and logs monitoring metrics. This implements the flow described in your project brief. 

## Features
- LLM function‑calling (OpenAI) with mock fallback.
- Guardrails: SELECT/WITH only, blocklist, enforced LIMITs.
- Syntax verification via dialect‑aware `EXPLAIN`.
- Multi‑DB via SQLAlchemy (Postgres/MySQL/SQLite/MSSQL).
- Semantic KPI layer with YAML templates & aliases.
- Monitoring to SQLite with `/metrics` endpoint.
- Minimal HTML frontend.

## Quickstart
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp config.example.yaml config.yaml
# Edit config.yaml with your DB urls; optionally set an OpenAI key

uvicorn backend.main:app --reload --port 8000
# Open frontend/index.html in your browser
```

## Notes
- If no API key, a mock LLM produces simple queries so you can test the pipeline.
- Add your schema description to the UI's "schema hint" to improve SQL quality.
- Extend the semantic layer in `config.yaml -> semantic`.

## Tests
```
pytest
```
