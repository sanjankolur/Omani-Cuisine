from fastapi import APIRouter, HTTPException
from ..supabase_client import get_admin_supabase
from ..services.food import get_dish
router = APIRouter(prefix="/nutrition", tags=["Nutrition"])

@router.get("/{dish_id}")
def nutrition(dish_id: str):
    dish = get_dish(dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")
    return {"dish_id": dish_id, "dish_name": dish.get("name"), "nutrition": dish.get("nutrition") or [], "disclaimer": "Values depend on recipe and serving size. Use verified ingredient quantities for precise calculations."}
