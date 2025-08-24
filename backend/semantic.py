from __future__ import annotations
from typing import Dict, Any, Tuple, Optional
import re

def resolve_kpi(user_text: str, cfg: Dict[str, Any]) -> Optional[str]:
    aliases = cfg.get("semantic", {}).get("kpi_aliases", {})
    lowered = user_text.lower()
    for canonical, words in aliases.items():
        if canonical in lowered:
            return canonical
        for w in words:
            if re.search(rf"\b{re.escape(w.lower())}\b", lowered):
                return canonical
    return None

def build_kpi_sql(canonical_kpi: str, time_grain: str, start_date: str, end_date: str,
                  filters_sql: str, cfg: Dict[str, Any]) -> Optional[str]:
    templates = cfg.get("semantic", {}).get("kpis", {})
    templ = templates.get(canonical_kpi)
    if not templ:
        return None
    templ = templ.replace("{time_grain}", time_grain)
    templ = templ.replace("{start_date}", ":start_date")
    templ = templ.replace("{end_date}", ":end_date")
    templ = templ.replace("{filters}", f" AND {filters_sql}" if filters_sql else "")
    return templ

def extract_date_range(user_text: str) -> Tuple[str, str]:
    # naive default: last 30 days (example dates; adjust live)
    return ("2025-07-26", "2025-08-24")

def extract_filters(user_text: str) -> str:
    if "apac" in user_text.lower():
        return "region = 'APAC'"
    return ""
