"""Builds the per-project document mind map: project hub -> documents -> their items, plus cross-document links.
Pure presentation of facts already in the graph; nothing here verifies anything."""
from graph import is_current

RANK = {"PASS": 0, "AGENT": 1, "FAIL": 2}
SHORT = {"contract": lambda x, d: x.id.split(":", 1)[-1], "spec": lambda x, d: x.id.removeprefix(d.id + "-")}

def build_mindmap(name, corpus, G, triples, rows):
    state = {r.triple_id: r.status for r in rows}
    worst = {}                                    # item id -> worst audit status of any check that touches it
    for t in triples:
        s = state[t.id]
        for n in (t.clause_id, t.spec_id, t.drawing_rev_id):
            if n and RANK[s] >= RANK.get(worst.get(n), -1): worst[n] = s
    branches = []
    for d in corpus.documents:
        if d.kind == "contract": items = [(x.id, SHORT["contract"](x, d), x.text, False) for x in corpus.clauses if x.doc_id == d.id]
        elif d.kind == "spec": items = [(x.id, SHORT["spec"](x, d), x.text, False) for x in corpus.spec_reqs if x.doc_id == d.id]
        else: items = [(r.id, f"Rev {r.revision}", f"{r.drawing_id} Rev {r.revision}, {r.date}", not is_current(G, r.id))
                       for r in corpus.drawing_revs if r.drawing_id == d.id]
        branches.append(dict(id=d.id, kind=d.kind, title=d.title,
                             children=[dict(id=i, label=l, text=t, superseded=s, status=worst.get(i)) for i, l, t, s in items]))
    links, seen = [], set()
    def add(a, b, rel):
        if (a, b, rel) not in seen: seen.add((a, b, rel)); links.append(dict(source=a, target=b, rel=rel))
    for u, v, e in G.edges(data=True):
        if e["rel"] in ("REFERENCES", "CITES", "SUPERSEDES"): add(u, v, e["rel"])       # clause->spec, clause->revision, newer->older
        elif e["rel"] == "COVERS":                                                      # spec -> (callout) -> drawing revision
            for rev in G.successors(v):
                if G.edges[v, rev]["rel"] == "ON": add(u, rev, "COVERS")
    return dict(project=name, branches=branches, links=links)
