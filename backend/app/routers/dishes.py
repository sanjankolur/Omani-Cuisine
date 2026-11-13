from fastapi import APIRouter, HTTPException, Query
from ..services.food import list_dishes, get_dish
router = APIRouter(prefix="/dishes", tags=["Dishes"])

@router.get("")
def dishes(search: str | None = None, region: str | None = None, limit: int = Query(50, ge=1, le=200)):
    return {"items": list_dishes(search, region, limit)}

@router.get("/{dish_id}")
def dish_detail(dish_id: str):
    item = get_dish(dish_id)
    if not item:
        raise HTTPException(status_code=404, detail="Dish not found")
    return item
