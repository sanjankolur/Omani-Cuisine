from fastapi import APIRouter
from ..dependencies import OptionalUser
from ..services.food import list_dishes

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("")
def analytics(user: OptionalUser = None):
    dishes = list_dishes(limit=200)
    categories = {}
    regions = {}
    for dish in dishes:
        category = dish.get("category") or "Other"
        region = dish.get("region") or "Unspecified"
        categories[category] = categories.get(category, 0) + 1
        regions[region] = regions.get(region, 0) + 1
    return {
        "total_dishes": len(dishes),
        "categories": categories,
        "regions": regions,
        "top_regions": sorted(regions.items(), key=lambda item: item[1], reverse=True)[:5],
        "popular_items": dishes[:5],
    }
