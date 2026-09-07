"""
Manual pipeline test script.

Run this WHILE `uvicorn app.main:app --reload --port 8000` is already
running in another terminal:

    python test_pipeline_manual.py
"""
import json
import requests

BASE_URL = "http://localhost:8000"

def call_process(submission):
    response = requests.post(f"{BASE_URL}/process", json=submission)
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print("-" * 60)
    return response.json()

def make_submission(sub_id, title, description, district="Ranchi", village="Hesag"):
    return {
        "submission_id": sub_id,
        "submitted_by": {"user_id": "USR-TEST", "role": "citizen"},
        "input_type": "text",
        "content": {"title": title, "description": description, "language": "en"},
        "location": {
            "state": "Jharkhand", "district": district, "area_type": "rural",
            "block": "Ratu", "panchayat_id": "PRI-0231", "village": village,
            "pincode": "834005",
            "coordinates": {"lat": 23.3441, "lng": 85.3096},
            "address_text": "Test address",
        },
        "media": [],
        "submitted_at": "2026-09-07T10:32:00Z",
    }

print("=== TEST 1: health check ===")
try:
    print(requests.get(f"{BASE_URL}/health").json())
except requests.exceptions.ConnectionError:
    print("ERROR: Could not connect. Is the FastAPI server running?")
    exit(1)
print()

print("=== TEST 2: Advisory (Known issue, standard solution) ===")
sub1 = make_submission(
    "SUB-TEST-A",
    "Yellow leaves on tomato plants",
    "The lower leaves of my tomato plants are turning yellow and have brown spots. This happens every monsoon season.",
)
result1 = call_process(sub1)
print(f"Expected outcome: 'advisory'. Got: '{result1.get('outcome', 'MISSING')}'")
print()

print("=== TEST 3: Doubtful (Potentially research-worthy, needs verification) ===")
sub2 = make_submission(
    "SUB-TEST-B",
    "Fish dying suddenly in village pond",
    "Over the last three days, dozens of fish are floating dead in the main panchayat pond. The water looks slightly greenish but there is no unusual smell. Not sure if it's a disease or water poisoning.",
)
result2 = call_process(sub2)
print(f"Expected outcome: 'doubtful'. Got: '{result2.get('outcome', 'MISSING')}'")
print()

print("=== TEST 4: Routed (Hard engineering/research problem) ===")
# The ORIGINAL severe engineering problem that gets routed to experts.
sub3 = make_submission(
    "SUB-TEST-Z",
    "Submersible pumps failing at 250ft due to heavy iron silt clogging",
    "Groundwater levels have dropped below 200ft this year. Standard borewell pumps are pulling up heavy iron-rich silt which destroys the impellers within weeks. Standard mesh filters clog in 48 hours, and cleaning them requires lifting the entire 250ft pipe assembly. We need a new type of self-cleaning filtration tool or centrifugal separator that can operate deep underground without relying on continuous electricity, as we face 12-hour power cuts.",
    village="Hesag"
)
result3 = call_process(sub3)
print(f"Expected outcome: 'routed'. Got: '{result3.get('outcome', 'MISSING')}'")
print()

print("=== TEST 5: Duplicate (Near-identical problem from same region) ===")
# A semantically similar report from a neighboring village.
# Because Test 4 is already routed, the NLP should catch this as a duplicate issue.
sub4 = make_submission(
    "SUB-TEST-D",
    "Motors breaking from deep mud, filters blocking",
    "Our borewell motors at 240ft are getting jammed by red iron mud. The normal filters get blocked in 2 days and pulling up the 240ft pipe manually without electricity is impossible. We need a permanent filter solution down there.",
    village="Kathal More"  # Slightly different location, but same systemic issue
)
result4 = call_process(sub4)
print(f"Expected outcome: 'duplicate'. Got: '{result4.get('outcome', 'MISSING')}'")
print()

print("ALL TESTS RAN — check the outcomes above against what's expected.")