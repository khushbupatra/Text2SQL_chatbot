from __future__ import annotations
from typing import Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

DDL = """
CREATE TABLE IF NOT EXISTS interactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  user_text TEXT,
  db_key TEXT,
  generated_sql TEXT,
  valid INTEGER,
  blocked_reason TEXT,
  latency_ms INTEGER,
  rows_returned INTEGER,
  verified INTEGER,
  error TEXT
);
"""

class Monitor:
    def __init__(self, url: str):
        self.engine: Engine = create_engine(url, future=True)
        with self.engine.begin() as conn:
            conn.exec_driver_sql(DDL)

    def log(self, **kwargs):
        cols = ",".join(kwargs.keys())
        vals = ",".join([f":{k}" for k in kwargs.keys()])
        with self.engine.begin() as conn:
            conn.execute(text(f"INSERT INTO interactions ({cols}) VALUES ({vals})"), kwargs)

    def stats(self) -> Dict[str, Any]:
        q = """
        SELECT COUNT(*) AS total,
               SUM(valid) AS valid_count,
               SUM(verified) AS verified_count,
               SUM(CASE WHEN error IS NOT NULL AND error != '' THEN 1 ELSE 0 END) AS errors
        FROM interactions
        """
        with self.engine.begin() as conn:
            row = conn.execute(text(q)).mappings().first()
            return dict(row or {})
