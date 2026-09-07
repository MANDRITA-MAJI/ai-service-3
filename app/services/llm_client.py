import os
import json
from groq import Groq

_client = None

# Free-tier friendly: fast, and rate limits (30 RPM on the free tier as of
# writing) are generous enough for a live demo. Swap to
# "llama-3.3-70b-versatile" in this one place if you want higher-quality
# answers and can live with tighter limits — nothing else needs to change.
GROQ_MODEL = "llama-3.1-8b-instant"


def get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Get a free key at console.groq.com "
                "(no credit card needed) and add it to your .env file."
            )
        _client = Groq(api_key=api_key)
    return _client


def call_json(system_prompt: str, user_prompt: str) -> dict:
    """Every LLM call in this service wants strict JSON back — this is the
    one place that makes the request and parses it, so classification and
    triage don't duplicate this logic."""
    client = get_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    raw = response.choices[0].message.content
    return json.loads(raw)
