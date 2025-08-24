from __future__ import annotations
from typing import Dict, Any, Tuple
import re
import sqlparse

DANGEROUS_DEFAULTS = {"drop", "delete", "truncate", "alter", "update", "insert"}

def normalize_sql(sql: str) -> str:
    return sql.strip().strip(";").strip()

def is_select_only(sql: str, allowed_verbs=("select","with")) -> bool:
    parsed = sqlparse.parse(sql)
    if not parsed:
        return False
    # Find first non-whitespace token value
    first = ""
    for tok in parsed[0].tokens:
        if not tok.is_whitespace:
            first = tok.value.lower()
            break
    return any(first.startswith(v) for v in allowed_verbs)

def contains_forbidden(sql: str, forbidden) -> bool:
    lowered = sql.lower()
    for kw in forbidden:
        if re.search(rf"\b{re.escape(kw)}\b", lowered):
            return True
    return False

def enforce_limit(sql: str, max_limit: int, default_limit: int) -> str:
    lowered = sql.lower()
    if " limit " in lowered or re.search(r"\btop\s+\d+\b", lowered):
        sql = re.sub(r"limit\s+\d+", f"limit {min(default_limit, max_limit)}", sql, flags=re.IGNORECASE)
        sql = re.sub(r"\btop\s+\d+\b", f"TOP {min(default_limit, max_limit)}", sql, flags=re.IGNORECASE)
        return sql
    return sql + f" LIMIT {min(default_limit, max_limit)}"

def validate_sql(sql: str, cfg: Dict[str, Any]) -> Tuple[bool, str, str]:
    sql = normalize_sql(sql)
    if not is_select_only(sql, tuple(cfg.get("guardrails", {}).get("allowed_verbs", ["select", "with"]))):
        return False, sql, "Only SELECT/WITH queries are allowed."
    forbidden = set(cfg.get("guardrails", {}).get("forbidden_keywords", [])) or DANGEROUS_DEFAULTS
    if contains_forbidden(sql, forbidden):
        return False, sql, "Query contains forbidden keywords."
    max_limit = int(cfg.get("guardrails", {}).get("max_limit", 500))
    default_limit = int(cfg.get("guardrails", {}).get("enforce_limit", 200))
    sql = enforce_limit(sql, max_limit, default_limit)
    return True, sql, ""
