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


def make_submission(sub_id, title, description, district="Ranchi"):
    return {
        "submission_id": sub_id,
        "submitted_by": {"user_id": "USR-TEST", "role": "citizen"},
        "input_type": "text",
        "content": {"title": title, "description": description, "language": "en"},
        "location": {
            "state": "Jharkhand", "district": district, "area_type": "rural",
            "block": "Ratu", "panchayat_id": "PRI-0231", "village": "Hesag",
            "pincode": "834005",
            "coordinates": {"lat": 23.3441, "lng": 85.3096},
            "address_text": "Test address",
        },
        "media": [],
        "submitted_at": "2026-09-06T10:32:00Z",
    }


print("=== TEST 1: health check ===")
print(requests.get(f"{BASE_URL}/health").json())
print()

print("=== TEST 2: a real, research-worthy problem ===")
sub1 = make_submission(
    "SUB-TEST-A",
    "Water pump broken near school",
    "The hand pump near the government school in ward 5 has been broken "
    "for 2 weeks despite repeated repairs, children are walking 1km for water",
)
result1 = call_process(sub1)
print(f"Expected outcome: 'routed'. Got: '{result1['outcome']}'")
print()

print("=== TEST 3: a near-duplicate of TEST 2 -> should be flagged 'duplicate' ===")
sub2 = make_submission(
    "SUB-TEST-B",
    "Pump not working",
    "Hand pump near the ward 5 school is broken, kids walking far for water",
)
result2 = call_process(sub2)
print(f"Expected outcome: 'duplicate'. Got: '{result2['outcome']}'")
print()

print("=== TEST 4: a likely-advisory problem (not research-worthy) ===")
sub3 = make_submission(
    "SUB-TEST-C",
    "My crop yield is low",
    "My crop yield is low this season, not sure why",
)
result3 = call_process(sub3)
print(f"Expected outcome: 'advisory' or 'doubtful'. Got: '{result3['outcome']}'")
print()

print("ALL TESTS RAN — check the outcomes above against what's expected.")