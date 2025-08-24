from __future__ import annotations
from typing import Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
import yaml, os

class DBRouter:
    def __init__(self, config: Dict[str, Any]):
        self.engines: Dict[str, Engine] = {}
        for key, db in config.get("databases", {}).items():
            url = db["url"]
            engine = create_engine(url, pool_pre_ping=True, future=True)
            self.engines[key] = engine

    def get(self, key: str) -> Engine:
        if key not in self.engines:
            raise KeyError(f"Unknown database key: {key}")
        return self.engines[key]

    def explain_prefix(self, engine: Engine) -> str:
        name = engine.dialect.name
        if name in ("postgresql", "postgres"):
            return "EXPLAIN "
        if name in ("mysql", "mariadb"):
            return "EXPLAIN "
        if name == "sqlite":
            return "EXPLAIN QUERY PLAN "
        if name in ("mssql", "sqlserver"):
            return "SET SHOWPLAN_ALL ON; "
        return "EXPLAIN "

def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
