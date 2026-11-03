# EPC Cross-Document Consistency Auditor (prototype)
Audits contract clauses, spec requirements and drawing revisions for cross-document inconsistencies. **Not a RAG chatbot**: a knowledge graph enumerates every clause–spec–drawing triple; each is verified by a deterministic rule where one exists, and only the residual goes to an LLM.

```
FileSource.load(folder) -> Corpus (Pydantic)   # sample project or uploaded files
        -> graph.py: NetworkX graph, enumerate triples, SUPERSEDES filter
        -> verify_deterministic.py   (PASS/FAIL, never calls an LLM)
        -> verify_agentic.py         (AGENT: only free-text triples)
        -> mindmap.py: per-project document map (documents, items, cross-document links)
        -> FastAPI (login required): /projects/{id}/audit|graph|mindmap|triples  ->  static dashboard
```
## Run locally
`python tools/generate_sample_project.py` (optional; needs python-docx, reportlab) regenerates the sample files.
`cd backend && pip install -r requirements.txt && uvicorn main:app --reload` then serve `frontend/` (e.g. `python -m http.server 8080` inside it) and open it; config.js points to localhost:8000. Set `GEMINI_API_KEY` to enable the agentic path.

## Login
Every route except `/health` and `/auth/login` needs a bearer token. Users come from the `AUTH_USERS` env var as `user:password` pairs separated by commas (passwords must not contain commas), e.g. `AUTH_USERS="alice:s3cret,bob:hunter2"`. Set `AUTH_SECRET` to any long random string so sessions survive a restart (Render generates one from `render.yaml`). If `AUTH_USERS` is unset the backend falls back to a built-in `demo` account and prints a warning, so always set it before deploying. This gates access; it is not a multi-user system (no sign-up, no per-user data, no database).

## Projects and the document map
The sample project is always available. **New project** uploads files as a named project, switchable from the header dropdown. Projects live in memory, so a restart returns to the sample project only. The **Document map** tab draws the selected project as a mind map: project hub, its documents, the items inside each (contract clauses, spec requirements, drawing revisions), and the links between documents (references, cites, covers, supersedes). Items are coloured by the worst audit result that touches them, and clicking one lists its checks and jumps to the trace.

## Input files
Contracts (.docx/.pdf/.txt) and specs with numbered clauses in the grammar documented in `ingestion/file_source.py`; `drawing_register.csv`; `callout_schedule.csv`. Upload them in the UI, or use the bundled sample project (`backend/corpus/sample_project`). `python backend/evaluate.py` scores the audit against planted deviations.

## Out of scope (deliberate)
Drawing content extraction (stubbed in `ingestion/drawing_extraction.py`), OCR, Docker, CI, a logging layer, a graph database.

## Beyond this input format
Messier real-world files need a more tolerant clause segmenter than the strict grammar here, and a connector must parse real files (PDF/Word contracts and specs via a clause segmenter that extracts parameter, value, unit, tolerance and cross-references; drawings via title-block/revision-table parsing plus the real `extract_callouts`) into the same `Corpus` models, resolve document IDs and revision lineage (setting `supersedes`), and handle intake (email/upload connector or SharePoint/DMS sync with auth and incremental updates). Graph and verifiers stay unchanged.
