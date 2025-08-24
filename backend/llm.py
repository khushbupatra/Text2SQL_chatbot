from __future__ import annotations
from typing import Dict, Any
import os, json

class LLMClient:
    """
    Minimal abstraction for an LLM with function-calling.
    If OPENAI_API_KEY or config llm.api_key is missing, falls back to a simple rule-based mock.
    """
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.provider = cfg.get("llm", {}).get("provider", "mock")
        self.model = cfg.get("llm", {}).get("model", "gpt-4o-mini")
        self.api_key = cfg.get("llm", {}).get("api_key") or os.getenv("OPENAI_API_KEY")
        self.use_mock = (self.provider != "openai") or (not self.api_key)

    def call_generate_sql(self, user_text: str, schema_hint: str = "") -> str:
        """
        Returns a SQL string from user_text using function-calling style.
        """
        if self.use_mock:
            lower = user_text.lower()
            if "customers" in lower:
                return "SELECT * FROM customers ORDER BY spend DESC LIMIT 10"
            if "orders" in lower:
                return "SELECT * FROM orders LIMIT 50"
            return "SELECT 1 as mock"
        try:
            import httpx
            fn_schema = {
                "name": "generate_sql",
                "description": "Generate a safe, read-only SQL query for the user's NL question.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string", "description": "The SQL query to run (SELECT-only)."}
                    },
                    "required": ["sql"]
                }
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You convert natural language into SQL for analytics. Use only SELECT or WITH."},
                    {"role": "user", "content": user_text},
                    {"role": "system", "content": f"Schema hint:\n{schema_hint[:4000]}"}
                ],
                "tools": [{"type": "function", "function": fn_schema}],
                "tool_choice": {"type": "function", "function": {"name": "generate_sql"}}
            }
            headers = {"Authorization": f"Bearer {self.api_key}"}
            r = httpx.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=60)
            r.raise_for_status()
            data = r.json()
            tool_calls = data["choices"][0]["message"].get("tool_calls", [])
            if tool_calls:
                args = tool_calls[0]["function"]["arguments"]
                parsed = json.loads(args)
                return parsed.get("sql", "SELECT 1")
            return "SELECT 1"
        except Exception:
            return "SELECT 1"
