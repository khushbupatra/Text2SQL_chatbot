from backend.guardrails import validate_sql
import yaml

cfg = yaml.safe_load('guardrails:\n  forbidden_keywords: ["drop"]\n  enforce_limit: 50\n  max_limit: 100\n')

def test_select_ok():
    ok, sql, reason = validate_sql("SELECT * FROM t", cfg)
    assert ok and "limit" in sql.lower()

def test_forbidden():
    ok, sql, reason = validate_sql("DROP TABLE t", cfg)
    assert not ok and "forbidden" in reason.lower()
