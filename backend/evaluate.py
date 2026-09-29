"""Scores the audit against the known-answer manifest of planted deviations. Run: python evaluate.py"""
import json
import main
from pathlib import Path
main.run_pipeline(str(main.SAMPLE)); S = main.STATE
m = json.load(open(main.SAMPLE / "_manifest.json")); lo = lambda s: s.lower()
fail = {lo(r.parameter) for r in S["rows"] if r.status == "FAIL"}
exp = set(m["expected_numeric_fail"]) | set(m["expected_revision_fail"])
sem = {lo(r.parameter) for r in S["rows"] if r.status == "AGENT" and r.explanation.startswith("INCONSISTENT")}
gaps = {lo(g["parameter"]) for g in S["gaps"]}
print(f"rows={len(S['rows'])} pass={sum(r.status=='PASS' for r in S['rows'])} fail={len(fail)} agent={sum(r.status=='AGENT' for r in S['rows'])}")
print("deterministic FAIL   missed:", exp - fail, "| false alarms:", fail - exp)
print("superseded excluded  expected", m["expected_superseded_excluded"], "got", len(S["excluded"]))
print("coverage gaps        missed:", set(m["expected_coverage_gaps"]) - gaps, "| extra:", gaps - set(m["expected_coverage_gaps"]))
print("semantic (needs API key) flagged:", sem, "expected:", set(m["expected_semantic_inconsistent"]))
print("ingestion:", S["stats"], "warnings:", S["warnings"])
