"""
Optional AI narrative layer. Purely additive: if GEMINI_API_KEY is set in
.env, this adds a short natural-language summary on top of the rule-based
insights. If no key is configured (or the call fails for any reason), the
app keeps working perfectly using the deterministic rule-based insights
computed in analysis.py.
"""
import os

from dotenv import load_dotenv

load_dotenv()

_GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()


def generate_ai_summary(overview: dict, insights: list[str]) -> str | None:
    if not _GEMINI_KEY:
        return None
    try:
        import google.generativeai as genai

        genai.configure(api_key=_GEMINI_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = (
            "You are a data analyst. In 3-4 concise sentences, summarize this "
            "dataset for a non-technical stakeholder. Do not invent numbers not given.\n\n"
            f"Rows: {overview['rows']}, Columns: {overview['columns']}, "
            f"Missing: {overview['missing_pct']}%, Duplicates: {overview['duplicate_rows']}.\n"
            f"Automated findings: {'; '.join(insights)}"
        )
        response = model.generate_content(prompt)
        return (response.text or "").strip() or None
    except Exception:
        return None
