"""Builds the NetworkX knowledge graph and enumerates every check (triple)."""
import networkx as nx
from models import Corpus, Triple

norm = lambda s: " ".join(s.lower().split())

def build_graph(c: Corpus) -> nx.DiGraph:
    G = nx.DiGraph()
    for d in c.documents: G.add_node(d.id, type="document", label=d.title, obj=d)
    for x in c.clauses: G.add_node(x.id, type="clause", label=x.id, obj=x)
    for s in c.spec_reqs: G.add_node(s.id, type="spec", label=s.id, obj=s)
    for r in c.drawing_revs: G.add_node(r.id, type="drawing_rev", label=f"{r.drawing_id} Rev {r.revision}", obj=r)
    for k in c.callouts: G.add_node(k.id, type="callout", label=k.id, obj=k)
    for x in c.clauses:
        if x.spec_ref in G: G.add_edge(x.id, x.spec_ref, rel="REFERENCES")          # dangling refs are reported as ingestion warnings + gaps
        if x.cites_drawing_rev in G: G.add_edge(x.id, x.cites_drawing_rev, rel="CITES")
    for r in c.drawing_revs:
        if r.supersedes: G.add_edge(r.id, r.supersedes, rel="SUPERSEDES")   # newer -> older
    for k in c.callouts:
        if k.drawing_rev_id in G: G.add_edge(k.id, k.drawing_rev_id, rel="ON")
        for s in c.spec_reqs:
            if norm(s.parameter) == norm(k.parameter): G.add_edge(s.id, k.id, rel="COVERS")
    return G

def is_current(G, rev_id: str) -> bool:
    """A revision is current iff nothing SUPERSEDES it."""
    return not any(G.edges[u, rev_id]["rel"] == "SUPERSEDES" for u in G.predecessors(rev_id))

def latest_revision(G, rev_id: str) -> str:
    """Follow SUPERSEDES edges forward to the newest revision id."""
    while not is_current(G, rev_id):
        rev_id = next(u for u in G.predecessors(rev_id) if G.edges[u, rev_id]["rel"] == "SUPERSEDES")
    return rev_id

def enumerate_triples(G):
    """Return (triples to verify, triples excluded as superseded, coverage gaps = clauses with nothing to verify against)."""
    triples, excluded, gaps = [], [], []
    for n, a in G.nodes(data=True):
        if a["type"] != "clause": continue
        cl = a["obj"]
        if cl.kind == "revision" and cl.cites_drawing_rev not in G:
            gaps.append(dict(clause_id=n, parameter=cl.parameter, reason="cited revision not in drawing register")); continue
        if cl.kind == "revision":
            triples.append(Triple(id=f"T-{n}", kind="revision", clause_id=n, drawing_rev_id=cl.cites_drawing_rev)); continue
        mine, old = [], []
        for spec in [m for m in G.successors(n) if G.edges[n, m]["rel"] == "REFERENCES"]:
            for cal in [m for m in G.successors(spec) if G.edges[spec, m]["rel"] == "COVERS"]:
                rev = next((m for m in G.successors(cal)), None)
                if rev is None: continue
                sp, ca = G.nodes[spec]["obj"], G.nodes[cal]["obj"]
                closed_form = cl.kind == "numeric" and sp.kind == "numeric" and ca.value is not None
                t = Triple(id=f"T-{n}-{cal}", kind="numeric" if closed_form else "free_text", clause_id=n, spec_id=spec, drawing_rev_id=rev, callout_id=cal)
                (mine if is_current(G, rev) else old).append(t)
        triples += mine; excluded += old
        if not mine:
            why = "only superseded drawing callouts" if old else "unknown spec reference" if not cl.spec_ref or cl.spec_ref not in G else "no drawing callout for this requirement"
            gaps.append(dict(clause_id=n, parameter=cl.parameter, reason=why))
    return triples, excluded, gaps
