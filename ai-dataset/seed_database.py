"""
Seed script to ingest curated Omani dishes & nutrition data into Supabase.
Run with:
    cd backend
    .\venv\Scripts\python.exe ..\ai-dataset\seed_database.py
"""
import sys
import os
import json
from pathlib import Path

# Add backend directory to sys.path so we can reuse app.supabase_client and app.config
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# pyrefly: ignore[missing-import]
from app.supabase_client import get_admin_supabase

def seed():
    raw_data_file = Path(__file__).resolve().parent / "raw_data" / "omani_dishes.json"
    if not raw_data_file.exists():
        print(f"Error: {raw_data_file} not found.")
        return

    with open(raw_data_file, "r", encoding="utf-8") as f:
        dishes = json.load(f)

    db = get_admin_supabase()
    print(f"Loaded {len(dishes)} dishes from {raw_data_file.name}. Syncing with Supabase...")

    for dish in dishes:
        nutrition = dish.pop("nutrition", None)
        
        # Upsert dish record
        res = db.table("dishes").upsert(dish, on_conflict="name").execute()
        dish_record = res.data[0] if res.data else None
        
        if not dish_record:
            # If already exists, fetch its id
            fetch = db.table("dishes").select("id").eq("name", dish["name"]).execute()
            if fetch.data:
                dish_record = fetch.data[0]

        if dish_record and nutrition:
            nutrition["dish_id"] = dish_record["id"]
            db.table("nutrition").upsert(nutrition, on_conflict="dish_id").execute()

        print(f"  ✓ Synced: {dish['name']} ({dish.get('name_ar', '')})")

    print("\n✅ Database seed completed successfully!")

if __name__ == "__main__":
    seed()

