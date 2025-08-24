from __future__ import annotations
import time, os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .db import DBRouter, load_config
from .guardrails import validate_sql
from .sqlgen import generate_sql
from .monitor import Monitor

CONFIG_PATH = os.environ.get("TEXT2SQL_CONFIG", os.path.join(os.path.dirname(__file__), "config.yaml"))
if not os.path.exists(CONFIG_PATH):
    example = os.path.join(os.path.dirname(__file__), "config.example.yaml")
    if os.path.exists(example):
        with open(example, "r", encoding="utf-8") as fsrc, open(CONFIG_PATH, "w", encoding="utf-8") as fdst:
            fdst.write(fsrc.read())

cfg = load_config(CONFIG_PATH)
router = DBRouter(cfg)
monitor = Monitor(cfg.get("monitoring", {}).get("db_url", "sqlite:///./metrics.db"))

app = FastAPI(title="AI Text-to-SQL Chatbot", version="1.0.0")

class AskRequest(BaseModel):
    user_text: str = Field(..., description="Natural-language question")
    db_key: str = Field(..., description="Which database to use (matches config key)")
    schema_hint: str = Field("", description="Optional schema/tables/columns context")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/schemas")
def schemas():
    return {"databases": list(router.engines.keys())}

@app.get("/metrics")
def metrics():
    return monitor.stats()

@app.post("/ask")
def ask(req: AskRequest):
    t0 = time.time()
    engine = router.get(req.db_key)

    sql = generate_sql(req.user_text, cfg, schema_hint=req.schema_hint or "")
    valid, sanitized_sql, reason = validate_sql(sql, cfg)
    if not valid:
        monitor.log(ts=time.strftime("%Y-%m-%d %H:%M:%S"),
                    user_text=req.user_text, db_key=req.db_key,
                    generated_sql=sql, valid=0, blocked_reason=reason,
                    latency_ms=int((time.time()-t0)*1000), rows_returned=0, verified=0, error="")
        raise HTTPException(400, f"Blocked for safety: {reason}")

    explain_prefix = router.explain_prefix(engine)
    verified = 0
    try:
        with engine.begin() as conn:
            if explain_prefix.strip().lower().startswith("set showplan_all"):
                conn.exec_driver_sql("SET SHOWPLAN_ALL ON;")
                conn.exec_driver_sql(sanitized_sql)
                conn.exec_driver_sql("SET SHOWPLAN_ALL OFF;")
            else:
                conn.exec_driver_sql(explain_prefix + sanitized_sql)
        verified = 1
    except SQLAlchemyError:
        verified = 0

    rows = []
    error = ""
    try:
        with engine.begin() as conn:
            res = conn.execute(text(sanitized_sql))
            cols = list(res.keys())
            for r in res.fetchall():
                rows.append(dict(zip(cols, r)))
    except SQLAlchemyError as e:
        error = str(e)

    latency = int((time.time() - t0) * 1000)
    monitor.log(ts=time.strftime("%Y-%m-%d %H:%M:%S"),
                user_text=req.user_text, db_key=req.db_key,
                generated_sql=sanitized_sql, valid=1, blocked_reason="",
                latency_ms=latency, rows_returned=len(rows), verified=verified, error=error)

    if error:
        raise HTTPException(400, f"Execution error: {error}")

    return {"sql": sanitized_sql, "verified": bool(verified), "rows": rows, "latency_ms": latency}
