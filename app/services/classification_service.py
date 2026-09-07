import json
from app.config import DATA_DIR
from app.services.llm_client import call_json

with open(DATA_DIR / "category_weights.json", encoding="utf-8") as f:
    _weights = json.load(f)

# pulled from category_weights.json so classification and priority scoring
# can never drift apart on what category names are valid
VALID_CATEGORIES = [c for c in _weights.keys() if c != "uncategorized"]

SYSTEM_PROMPT = (
    "You classify citizen-submitted civic problems into thematic categories "
    "for a government innovation platform. Always respond with strict JSON "
    "only, no extra text, no markdown formatting."
)


def classify_problem(text: str) -> dict:
    user_prompt = f"""Problem: "{text}"

Classify this problem into one or more of these categories (multi-label —
a problem can belong to more than one, but list at most 3):
{", ".join(VALID_CATEGORIES)}

Return JSON in exactly this shape:
{{
  "categories": [
    {{"label": "<category>", "confidence": <0.0-1.0>}}
  ],
  "primary_category": "<the single best-fit category from the list above>"
}}"""

    try:
        result = call_json(SYSTEM_PROMPT, user_prompt)
        if result.get("primary_category") not in VALID_CATEGORIES:
            raise ValueError("LLM returned a category outside the allowed list")
        return result
    except Exception as e:
        # fail safe, not fail loud — an uncategorized problem still flows
        # through the rest of the pipeline with a neutral default weight
        print(f"[classification_service] LLM call failed: {e}")
        return {
            "categories": [{"label": "uncategorized", "confidence": 0.0}],
            "primary_category": "uncategorized",
        }