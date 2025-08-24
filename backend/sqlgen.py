from __future__ import annotations
from typing import Dict, Any
from .llm import LLMClient
from .semantic import resolve_kpi, build_kpi_sql, extract_date_range, extract_filters

def maybe_generate_via_semantic_layer(user_text: str, cfg: Dict[str, Any]) -> str | None:
    kpi = resolve_kpi(user_text, cfg)
    if not kpi:
        return None
    start_date, end_date = extract_date_range(user_text)
    filters = extract_filters(user_text)
    sql = build_kpi_sql(kpi, time_grain="day", start_date=start_date, end_date=end_date,
                        filters_sql=filters, cfg=cfg)
    return sql

def generate_sql(user_text: str, cfg: Dict[str, Any], schema_hint: str = "") -> str:
    s = maybe_generate_via_semantic_layer(user_text, cfg)
    if s:
        return s
    llm = LLMClient(cfg)
    return llm.call_generate_sql(user_text, schema_hint=schema_hint)
