import httpx
from pathlib import Path

ROOT = Path("ai-dataset/split_data/test")
classes = sorted([d.name for d in ROOT.iterdir() if d.is_dir()])

print(f"Testing live FastAPI recognition endpoint on {len(classes)} classes:\n")
client = httpx.Client(timeout=30.0)

for cls_name in classes:
    sample_img = next((ROOT / cls_name).glob("*.jpg"), None)
    if not sample_img:
        continue
    with open(sample_img, "rb") as f:
        res = client.post(
            "http://127.0.0.1:8000/api/v1/recognize",
            files={"file": (sample_img.name, f.read(), "image/jpeg")}
        )
    if res.status_code == 200:
        d = res.json()
        p_name = d.get("dish_name", "Unknown")
        conf_pct = d.get("confidence_percentage", 0)
        conf_lbl = d.get("confidence", "low")
        has_db = bool(d.get("matched_dish"))
        print(f"  {cls_name:<20} -> {p_name:<16} | Conf: {conf_pct:>5.1f}% ({conf_lbl:<6}) | DB: {has_db}")
    else:
        print(f"  {cls_name:<20} -> Error {res.status_code}: {res.text}")
