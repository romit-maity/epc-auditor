# Decision log
| Date | Decision | Why (one line) |
|---|---|---|
| 2026-09-29 | Deterministic verifier and LLM fallback in separate files | Boundary is visible from folder structure alone; verifier has zero LLM imports |
| 2026-09-29 | NetworkX in-memory graph (would use Neo4j at production scale) | Corpus is tiny; a hosted graph DB is one more thing to deploy and explain |
| 2026-09-29 | Revision precedence is a graph fact: `newer -SUPERSEDES-> older` | "Current" = no incoming SUPERSEDES; drives both triple filtering and the currency rule |
| 2026-09-29 | Triples enumerated from graph edges (clause→spec→callout), not searched | Check-space is explicit and countable; nothing is skipped silently |
| 2026-09-29 | Drawing sheets registered but not read; callouts come from a callout-schedule CSV | Deliberate scope cut (no OCR/CAD); a dimension schedule is a real EPC artifact; `extract_callouts` is the stub to fill later |
| 2026-09-29 | Numeric rule checks contract↔spec AND drawing↔spec against the spec tolerance | Spec is the authority; catches both drift directions |
| 2026-09-29 | Free-text triples route to the LLM; no key → "UNCERTAIN, human review" | Never fabricate a verdict; app still runs without credentials |
| 2026-09-29 | No logging subsystem; API returns results directly | Simplest to explain; rows already carry rule + explanation as evidence |
| 2026-09-29 | Backend on Render, frontend on Netlify | Render: free Python web service from GitHub via render.yaml. Netlify: static site, env var injected at build into config.js |
| 2026-09-29 | Frontend is dependency-free static HTML/JS, not an Antigravity project | Antigravity is an IDE I can't run; static output needs no build tooling and is trivially deployable |
| 2026-09-29 | Replaced the JSON corpus with real files: docx contract, PDF specs, PDF drawing sheets, CSV register + callout schedule | A single JSON felt forced; files exercise real parsing and let the demo run on uploads |
| 2026-09-29 | One `FileSource` used for both the bundled sample project and uploads | Same code path for demo and live upload; nothing in graph/verifiers knows where files came from |
| 2026-09-29 | Strict regex clause grammar; unmatched clauses are counted and reported, never guessed | Parsing stays deterministic and defensible; LLM is not allowed to invent structure |
| 2026-09-29 | Coverage gaps (clause with nothing to verify against) reported separately, not as PASS/FAIL | "Unverifiable" is a finding but not a verdict; silence would hide it |
| 2026-09-29 | Sample project generated with a known-answer manifest; `evaluate.py` scores deterministic results | Gives a defensible precision/recall answer instead of "it looks right" |
