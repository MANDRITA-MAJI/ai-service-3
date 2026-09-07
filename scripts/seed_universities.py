"""Run once (and again whenever universities.json changes):
    python scripts/seed_universities.py
"""
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.embedding_service import embed_text
from app.db.chroma_client import get_or_create_collection
from app.config import DATA_DIR


def seed():
    with open(DATA_DIR / "universities.json", encoding="utf-8") as f:
        universities = json.load(f)

    collection = get_or_create_collection("university_departments")

    for uni in universities:
        for dept in uni["departments"]:
            dept_text = ", ".join(dept["expertise_areas"])
            vector = embed_text(dept_text)
            doc_id = f"{uni['university_id']}::{dept['name']}"
            collection.upsert(
                embeddings=[vector],
                documents=[dept_text],
                metadatas=[{
                    "university_id": uni["university_id"],
                    "university_name": uni["name"],
                    "department": dept["name"],
                    "district": uni["location"]["district"],
                    "category": dept.get("primary_category", ""),
                    "specialization": dept_text,
                    "current_active_projects": dept.get("active_projects", 0),
                    "max_concurrent_projects": uni.get("max_concurrent_projects", 15),
                }],
                ids=[doc_id],
            )

    print(f"Seeded {collection.count()} department records")


if __name__ == "__main__":
    seed()
