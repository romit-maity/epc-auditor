"""FastAPI app: wires ingestion -> graph -> deterministic verifier -> agentic fallback."""
import shutil, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from models import AuditRow
from ingestion.file_source import FileSource
from graph import build_graph, enumerate_triples, latest_revision
import verify_deterministic as det, verify_agentic as agent

SAMPLE = Path(__file__).parent / "corpus" / "sample_project"
app = FastAPI(title="EPC Cross-Document Consistency Auditor")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
STATE = {"folder": str(SAMPLE)}

def fmt(v, unit): return "—" if v is None else f"{v:g} {unit or ''}".strip()
cap = lambda s: s[:1].upper() + s[1:]

def run_pipeline(folder: str):
    corpus = FileSource(folder).load(); G = build_graph(corpus)
    triples, excluded, gaps = enumerate_triples(G); obj = lambda n: G.nodes[n]["obj"]
    rows, pending = [], []                       # pass 1: deterministic. pass 2: agentic, only for what pass 1 could not close.
    for t in triples:
        cl, rev = obj(t.clause_id), obj(t.drawing_rev_id)
        if t.kind == "numeric":
            sp, cal = obj(t.spec_id), obj(t.callout_id)
            st, rule, why = det.check_numeric_tolerance(cl.value, sp.value, sp.tol, cal.value)
            rows.append(AuditRow(triple_id=t.id, status=st, check_type="TOLERANCE", parameter=cap(cl.parameter), contract_value=fmt(cl.value, cl.unit),
                                 spec_value=f"{fmt(sp.value, sp.unit)} ±{sp.tol:g}", drawing_value=fmt(cal.value, cal.unit), rule=rule, explanation=why,
                                 clause_text=cl.text, spec_text=sp.text, drawing_text=f"{rev.drawing_id} Rev {rev.revision}: {cal.text}"))
        elif t.kind == "revision":
            latest = obj(latest_revision(G, rev.id))
            st, rule, why = det.check_revision_currency(rev.revision, latest.revision, rev.drawing_id)
            rows.append(AuditRow(triple_id=t.id, status=st, check_type="REVISION", parameter=cap(cl.parameter), contract_value=f"Rev {rev.revision}",
                                 spec_value="—", drawing_value=f"Rev {latest.revision} (current)", rule=rule, explanation=why, clause_text=cl.text,
                                 spec_text="—", drawing_text=f"{rev.drawing_id} latest: Rev {latest.revision}, {latest.date}"))
        else:
            sp, cal = obj(t.spec_id), obj(t.callout_id)
            rows.append(AuditRow(triple_id=t.id, status="AGENT", check_type="SEMANTIC", parameter=cap(cl.parameter), contract_value="free text",
                                 spec_value="free text", drawing_value="free text", rule="", explanation="", clause_text=cl.text, spec_text=sp.text,
                                 drawing_text=f"{rev.drawing_id} Rev {rev.revision}: {cal.text}"))
            pending.append(rows[-1])
    with ThreadPoolExecutor(6) as ex:
        for r, (rule, why) in zip(pending, ex.map(lambda r: agent.resolve(r.clause_text, r.spec_text, r.drawing_text), pending)):
            r.rule, r.explanation = rule, why
    STATE.update(folder=folder, rows=rows, excluded=[t.id for t in excluded], gaps=gaps, warnings=corpus.warnings, stats=corpus.stats,
                 graph=dict(nodes=[dict(id=n, type=a["type"], label=a["label"]) for n, a in G.nodes(data=True)],
                            edges=[dict(source=u, target=v, rel=d["rel"]) for u, v, d in G.edges(data=True)],
                            triples={t.id: t.model_dump() for t in triples}))

def payload(): return {k: STATE[k] for k in ("rows", "excluded", "gaps", "warnings", "stats")}

@app.on_event("startup")
def startup(): run_pipeline(STATE["folder"])

@app.get("/health")
def health(): return {"ok": True}

@app.post("/audit/run")
def run_audit(): run_pipeline(STATE["folder"]); return payload()

@app.post("/upload")
async def upload(files: List[UploadFile] = File(...)):
    d = tempfile.mkdtemp()
    for f in files:
        with open(Path(d) / Path(f.filename).name, "wb") as out: shutil.copyfileobj(f.file, out)
    try: run_pipeline(d)
    except Exception as e: raise HTTPException(422, f"Could not ingest upload: {type(e).__name__}: {e}")
    return payload()

@app.post("/reset")
def reset(): run_pipeline(str(SAMPLE)); return payload()

@app.get("/audit")
def audit(): return payload()

@app.get("/graph")
def graph(): return STATE["graph"]

@app.get("/triples/{triple_id}")
def triple(triple_id: str):
    row = next((r for r in STATE["rows"] if r.triple_id == triple_id), None)
    if not row: raise HTTPException(404, "unknown triple")
    return {"row": row, "structure": STATE["graph"]["triples"][triple_id]}
