"""Deterministic rules. Pure functions, closed-form answers, NEVER calls an LLM."""

def check_numeric_tolerance(contract_val, spec_val, spec_tol, drawing_val):
    """PASS iff the contract value AND the drawing value both lie within spec_tol of the spec value."""
    dc, dd = abs(contract_val - spec_val), abs(drawing_val - spec_val)
    rule = f"|contract - spec| <= {spec_tol} and |drawing - spec| <= {spec_tol}"
    bad = []
    if dc > spec_tol + 1e-9: bad.append(f"contract deviates from spec by {dc:.2f}")
    if dd > spec_tol + 1e-9: bad.append(f"drawing deviates from spec by {dd:.2f}")
    if bad: return "FAIL", rule, "; ".join(bad) + f" (tolerance ±{spec_tol})"
    return "PASS", rule, f"contract Δ={dc:.2f}, drawing Δ={dd:.2f}, both within ±{spec_tol}"

def check_revision_currency(cited_rev: str, latest_rev: str, drawing_id: str):
    """PASS iff the drawing revision cited by the contract is the latest in the SUPERSEDES chain."""
    rule = "cited revision == head of SUPERSEDES chain"
    if cited_rev == latest_rev: return "PASS", rule, f"{drawing_id} Rev {cited_rev} is current"
    return "FAIL", rule, f"contract cites {drawing_id} Rev {cited_rev}, but Rev {latest_rev} supersedes it"
