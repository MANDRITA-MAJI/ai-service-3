import json
from datetime import datetime, timezone
from app.config import DATA_DIR

with open(DATA_DIR / "severity_keywords.json", encoding="utf-8") as f:
    SEVERITY_KEYWORDS = json.load(f)

with open(DATA_DIR / "category_weights.json", encoding="utf-8") as f:
    CATEGORY_WEIGHTS = json.load(f)


def keyword_severity_score(text: str) -> int:
    text_lower = text.lower()
    if any(kw in text_lower for kw in SEVERITY_KEYWORDS.get("high", [])):
        return 3
    if any(kw in text_lower for kw in SEVERITY_KEYWORDS.get("medium", [])):
        return 2
    return 1


def compute_priority(
    description: str,
    category: str,
    duplicate_count: int,
    submitted_at: str,
    has_media: bool,
) -> dict:
    score = 0.0
    score += min(duplicate_count * 0.5, 5)
    score += keyword_severity_score(description) * 2
    score += CATEGORY_WEIGHTS.get(category, 1)

    submitted_dt = datetime.fromisoformat(submitted_at.replace("Z", "+00:00"))
    days_open = (datetime.now(timezone.utc) - submitted_dt).days
    score += min(days_open * 0.1, 2)

    if has_media:
        score += 0.5

    score = round(score, 2)
    if score >= 7:
        tier = "high"
    elif score >= 4:
        tier = "medium"
    else:
        tier = "low"

    return {"score": score, "tier": tier}
