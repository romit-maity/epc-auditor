# EPC Cross-Document Consistency Auditor (prototype)
Audits contract clauses, spec requirements and drawing revisions for cross-document inconsistencies. **Not a RAG chatbot**: a knowledge graph enumerates every clause–spec–drawing triple; each is verified by a deterministic rule where one exists, and only the residual goes to an LLM.

```
FileSource.load(folder) -> Corpus (Pydantic)   # sample project or uploaded files
        -> graph.py: NetworkX graph, enumerate triples, SUPERSEDES filter
        -> verify_deterministic.py   (PASS/FAIL, never calls an LLM)
        -> verify_agentic.py         (AGENT: only free-text triples)
        -> FastAPI: /audit /audit/run /graph /triples/{id}  ->  static dashboard
```
## Run locally
`python tools/generate_sample_project.py` (optional; needs python-docx, reportlab) regenerates the sample files.
`cd backend && pip install -r requirements.txt && uvicorn main:app --reload` then open `frontend/index.html` (config.js points to localhost:8000). Set `ANTHROPIC_API_KEY` to enable the agentic path.

## Input files
Contracts (.docx/.pdf/.txt) and specs with numbered clauses in the grammar documented in `ingestion/file_source.py`; `drawing_register.csv`; `callout_schedule.csv`. Upload them in the UI, or use the bundled sample project (`backend/corpus/sample_project`). `python backend/evaluate.py` scores the audit against planted deviations.

## Out of scope (deliberate)
Drawing content extraction (stubbed in `ingestion/drawing_extraction.py`), OCR, Docker, CI, a logging layer, a graph database.

## Beyond this input format
Messier real-world files need a more tolerant clause segmenter than the strict grammar here, and a connector must parse real files (PDF/Word contracts and specs via a clause segmenter that extracts parameter, value, unit, tolerance and cross-references; drawings via title-block/revision-table parsing plus the real `extract_callouts`) into the same `Corpus` models, resolve document IDs and revision lineage (setting `supersedes`), and handle intake (email/upload connector or SharePoint/DMS sync with auth and incremental updates). Graph and verifiers stay unchanged.
