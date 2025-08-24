from backend.semantic import resolve_kpi, build_kpi_sql
import yaml

cfg = yaml.safe_load('semantic:\n  kpi_aliases: {revenue: ["sales"]}\n  kpis: {revenue: "SELECT * FROM fact_sales WHERE date BETWEEN :start_date AND :end_date {filters}"}\n')

def test_resolve():
    assert resolve_kpi("show me sales", cfg) == "revenue"

def test_build():
    s = build_kpi_sql("revenue","day","2025-01-01","2025-01-31","region = \'APAC\'", cfg)
    assert "region" in s and ":start_date" in s
