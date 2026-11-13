from fastapi import APIRouter
from ..schemas import RecommendationRequest
from ..dependencies import OptionalUser
from ..services.food import list_dishes
from ..supabase_client import get_admin_supabase
router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.post("")
def recommend(payload: RecommendationRequest, user: OptionalUser = None):
    dishes = list_dishes(limit=200)
    avoid = {x.lower() for x in payload.avoid_ingredients}
    prefs = {x.lower() for x in payload.dietary_preferences}
    ranked = []
    for dish in dishes:
        ingredients = [x.strip().lower() for x in (dish.get("ingredients_summary") or "").split(",")]
        if any(any(a in ingredient for ingredient in ingredients) for a in avoid):
            continue
        tags = {x.lower() for x in (dish.get("dietary_tags") or [])}
        if prefs and not prefs.issubset(tags):
            continue
        score = len(prefs.intersection(tags)) * 2
        if payload.goal and payload.goal.lower() in (dish.get("description") or "").lower():
            score += 1
        ranked.append((score, dish))
    ranked.sort(key=lambda x: x[0], reverse=True)
    results = [d for _, d in ranked[:payload.limit]]
    if user and user.get("id"):
        try:
            get_admin_supabase().table("recommendations").insert({"user_id": user["id"], "criteria": payload.model_dump(), "result_dish_ids": [d["id"] for d in results]}).execute()
        except Exception:
            pass
    return {"items": results, "message": "Recommendations are based on the available dish tags and ingredient data. Confirm allergens directly."}
