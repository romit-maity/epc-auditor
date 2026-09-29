"""LLM fallback. Only reached for free-text triples no symbolic rule can resolve."""
import json, os

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
RULE = "LLM semantic comparison of clause, spec and drawing note (no closed-form rule exists)"

def resolve(clause_text: str, spec_text: str, drawing_text: str):
    """Return (rule, explanation). Degrades gracefully if no API key is configured."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        return RULE, "UNCERTAIN - no ANTHROPIC_API_KEY configured; routed to human review"
    import anthropic
    prompt = ("Compare three EPC document excerpts for consistency.\n"
              f"CONTRACT: {clause_text}\nSPEC: {spec_text}\nDRAWING NOTE: {drawing_text}\n"
              'Reply with ONLY JSON: {"verdict":"CONSISTENT|INCONSISTENT|UNCERTAIN","reasoning":"<=40 words"}')
    try:
        msg = anthropic.Anthropic().messages.create(model=MODEL, max_tokens=300,
                                                    messages=[{"role": "user", "content": prompt}])
        d = json.loads(msg.content[0].text.strip().strip("`").removeprefix("json").strip())
        return RULE, f"{d['verdict']} - {d['reasoning']}"
    except Exception as e:
        return RULE, f"UNCERTAIN - LLM call failed ({type(e).__name__}); routed to human review"
