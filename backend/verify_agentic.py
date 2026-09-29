"""LLM fallback. Only reached for free-text triples no symbolic rule can resolve."""
import json, os

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
RULE = "LLM semantic comparison of clause, spec and drawing note (no closed-form rule exists)"

def resolve(clause_text: str, spec_text: str, drawing_text: str):
    """Return (rule, explanation). Degrades gracefully if no API key is configured."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return RULE, "UNCERTAIN - no GEMINI_API_KEY configured; routed to human review"
    
    from google import genai
    prompt = ("Compare three EPC document excerpts for consistency.\n"
              f"CONTRACT: {clause_text}\nSPEC: {spec_text}\nDRAWING NOTE: {drawing_text}\n"
              'Reply with ONLY JSON: {"verdict":"CONSISTENT|INCONSISTENT|UNCERTAIN","reasoning":"<=40 words"}')
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        text = response.text.strip().strip("`").removeprefix("json").strip()
        d = json.loads(text)
        return RULE, f"{d['verdict']} - {d['reasoning']}"
    except Exception as e:
        return RULE, f"UNCERTAIN - LLM call failed ({type(e).__name__}); routed to human review"