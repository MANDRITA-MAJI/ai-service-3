# AI Service — Societal Innovation Portal (SIH26043)

## Setup

```bash
pip install -r requirements.txt --break-system-packages
cp .env.example .env   # then add your free Groq key — console.groq.com, no credit card
python scripts/seed_universities.py     # run once, and again after editing data/universities.json
uvicorn app.main:app --reload --port 8000
```

Classification and research-vs-advisory triage run on Groq's free tier
(`llama-3.1-8b-instant`) — no per-request billing, and the free rate limit
(30 RPM as of writing) comfortably covers demo traffic. If you ever want
higher-quality answers and can live with tighter limits, swap the model
name in `app/services/llm_client.py` — nothing else needs to change.

## Endpoint contract (for the Next.js backend team)

### `POST /process`

Send this — the exact shape produced once a citizen's voice/text submission is
confirmed:

```json
{
  "submission_id": "SUB-2026-000482",
  "submitted_by": { "user_id": "USR-1029", "role": "citizen" },
  "input_type": "text",
  "content": {
    "title": "Water pump broken near school",
    "description": "The hand pump near the government school...",
    "language": "hi",
    "audio_url": null
  },
  "location": {
    "state": "Jharkhand", "district": "Ranchi", "area_type": "rural",
    "block": "Ratu", "panchayat_id": "PRI-0231", "village": "Hesag",
    "ulb_id": null, "ward_no": null, "pincode": "834005",
    "coordinates": { "lat": 23.3441, "lng": 85.3096 },
    "address_text": "Near Govt Primary School, Ward 5"
  },
  "media": [{ "type": "image", "url": "s3://.../img1.jpg" }],
  "submitted_at": "2026-09-06T10:32:00Z"
}
```

You get back one of three shapes, depending on `outcome`:

- **`outcome: "advisory"`** — only `classification` + `triage` are filled.
  Route this to the citizen's advisory channel; it never reaches a university.
- **`outcome: "duplicate"`** — `duplicate_info.similar_submission_ids` lists
  the matching existing problems. Increment their affected-citizen count;
  don't create a new routing/priority record for this one.
- **`outcome: "routed"`** — full pipeline ran. `priority` and
  `routing.shortlist` (ranked list of 5 universities) are populated.
  Only notify `shortlist[0]` first — walk down the list yourself on
  rejection, don't call this endpoint again for that.

### `GET /health`

Returns `{"status": "ok"}` — use for a startup check.

## What's fully working vs. still a stub

| Module | Status |
|---|---|
| Embedding | Working (`paraphrase-multilingual-MiniLM-L12-v2`) |
| Speech-to-text | Working (self-hosted `faster-whisper`, no API token limits) |
| Deduplication | Working (Chroma, cosine similarity) |
| University routing | Working (Chroma + hard-filter boosts) |
| Priority scoring | Working (keyword + category weighted formula) |
| Classification | Working (Groq `llama-3.1-8b-instant`, multi-label, categories pulled from `category_weights.json`) |
| Research-vs-advisory triage (LLM step) | Working (Groq, 3-way advisory/doubtful/research + `needs_govt_supervision`) |
| `/confirm-vague` (professor rejects a doubtful problem) | Working — reuses the already-stored embedding, no re-embedding or LLM call needed |

Every module runs real logic now. Both LLM calls fail safe, not fail loud:
if a Groq call errors or returns malformed JSON, classification falls back
to `"uncategorized"` and triage falls back to `"doubtful"` (never silently
auto-approves or auto-rejects a problem on a broken API call).
