"""FastAPI app: ingestion -> graph -> deterministic verifier -> agentic fallback, per project, behind login."""
import shutil, tempfile, time, uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from models import AuditRow
from ingestion.file_source import FileSource
from graph import build_graph, enumerate_triples, latest_revision
from mindmap import build_mindmap
import auth, verify_deterministic as det, verify_agentic as agent

SAMPLE = Path(__file__).parent / "corpus" / "sample_project"
app = FastAPI(title="EPC Cross-Document Consistency Auditor")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
PROJECTS: dict = {}                              # project id -> audit state; in memory, so a restart keeps only the sample project

def fmt(v, unit): return "—" if v is None else f"{v:g} {unit or ''}".strip()
cap = lambda s: s[:1].upper() + s[1:]

def run_pipeline(folder: str, pid: str = "sample", name: str = "Sample project"):
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
    PROJECTS[pid] = dict(id=pid, name=name, folder=folder, created=PROJECTS.get(pid, {}).get("created", time.time()), rows=rows,
                         excluded=[t.id for t in excluded], gaps=gaps, warnings=corpus.warnings, stats=corpus.stats,
                         graph=dict(nodes=[dict(id=n, type=a["type"], label=a["label"]) for n, a in G.nodes(data=True)],
                                    edges=[dict(source=u, target=v, rel=d["rel"]) for u, v, d in G.edges(data=True)],
                                    triples={t.id: t.model_dump() for t in triples}),
                         mindmap=build_mindmap(name, corpus, G, triples, rows))
    return PROJECTS[pid]

def project(pid: str):
    if pid not in PROJECTS: raise HTTPException(404, "unknown project")
    return PROJECTS[pid]

def payload(p): return {k: p[k] for k in ("id", "name", "rows", "excluded", "gaps", "warnings", "stats")}

def summary(p):
    n = lambda s: sum(r.status == s for r in p["rows"])
    return {"id": p["id"], "name": p["name"], "files": p["stats"].get("files", 0), "created": p["created"], "pass": n("PASS"), "fail": n("FAIL"), "agent": n("AGENT")}

class Login(BaseModel):
    username: str; password: str

@app.on_event("startup")
def startup(): run_pipeline(str(SAMPLE))

@app.get("/health")
def health(): return {"ok": True}

@app.post("/auth/login")
def login(body: Login): return auth.login(body.username.strip(), body.password)

api = APIRouter(dependencies=[Depends(auth.current_user)])    # everything below requires a valid token

@api.get("/auth/me")
def me(user: str = Depends(auth.current_user)): return {"user": user}

@api.get("/projects")
def projects(): return sorted((summary(p) for p in PROJECTS.values()), key=lambda s: (s["id"] != "sample", -s["created"]))

@api.post("/projects")
def create_project(name: str = Form(""), files: List[UploadFile] = File(...)):
    name = name.strip()[:60] or "Uploaded project " + time.strftime("%H:%M")
    d = tempfile.mkdtemp()
    for f in files:
        with open(Path(d) / Path(f.filename).name, "wb") as out: shutil.copyfileobj(f.file, out)
    pid = uuid.uuid4().hex[:8]
    try:
        p = run_pipeline(d, pid, name)
        if not p["mindmap"]["branches"]:                 # nothing recognisable: refuse rather than create an empty project
            raise ValueError("no contract, specification or drawing register recognised. " + "; ".join(p["warnings"][:3]))
        return summary(p)
    except Exception as e:
        PROJECTS.pop(pid, None); shutil.rmtree(d, ignore_errors=True)
        raise HTTPException(422, f"Could not ingest upload: {e}" if isinstance(e, ValueError) else f"Could not ingest upload: {type(e).__name__}: {e}")

@api.get("/projects/{pid}/audit")
def audit(pid: str): return payload(project(pid))

@api.post("/projects/{pid}/audit/run")
def run_audit(pid: str):
    p = project(pid); return payload(run_pipeline(p["folder"], pid, p["name"]))

@api.get("/projects/{pid}/graph")
def graph(pid: str): return project(pid)["graph"]

@api.get("/projects/{pid}/mindmap")
def mindmap(pid: str): return project(pid)["mindmap"]

@api.get("/projects/{pid}/triples/{triple_id}")
def triple(pid: str, triple_id: str):
    p = project(pid); row = next((r for r in p["rows"] if r.triple_id == triple_id), None)
    if not row: raise HTTPException(404, "unknown triple")
    return {"row": row, "structure": p["graph"]["triples"][triple_id]}

app.include_router(api)
