from ..config import settings
from ..supabase_client import get_admin_supabase

DEMO_DISHES = [
    {
        "id": "demo-shuwa",
        "name": "Omani Shuwa",
        "name_ar": "شوا",
        "category": "Meat",
        "region": "Across Oman",
        "description": "Marinated meat traditionally slow-cooked for many hours in an underground oven.",
        "ingredients_summary": "lamb, garlic, spices, vinegar",
        "cooking_method": "Slow-cooked in a sealed underground oven.",
        "cultural_notes": "Often prepared for Eid and family celebrations.",
        "dietary_tags": ["high protein", "comfort food", "festive"],
    },
    {
        "id": "demo-majboos",
        "name": "Majboos",
        "name_ar": "مجبوس",
        "category": "Rice",
        "region": "Across Oman",
        "description": "A fragrant spiced rice dish commonly served with chicken, lamb, or fish.",
        "ingredients_summary": "rice, chicken, onion, tomato, baharat, lime",
        "cooking_method": "Rice simmered with spiced meat or fish.",
        "cultural_notes": "A much-loved celebratory and family meal.",
        "dietary_tags": ["comfort food", "festive", "high protein"],
    },
    {
        "id": "demo-harees",
        "name": "Harees",
        "name_ar": "هريس",
        "category": "Wheat",
        "region": "Across Oman",
        "description": "A comforting dish of wheat and meat cooked until soft and blended.",
        "ingredients_summary": "wheat, chicken, lamb, salt, ghee",
        "cooking_method": "Slow-cooked and stirred to a porridge-like texture.",
        "cultural_notes": "Often associated with Ramadan and gatherings.",
        "dietary_tags": ["comfort food", "family meal"],
    },
    {
        "id": "demo-halwa",
        "name": "Omani Halwa",
        "name_ar": "حلاوة عمانية",
        "category": "Dessert",
        "region": "Across Oman",
        "description": "A traditional gelatinous sweet often flavoured with rosewater, saffron, and spices.",
        "ingredients_summary": "sugar, starch, rosewater, saffron, nuts",
        "cooking_method": "Slow-stirred until thick and glossy.",
        "cultural_notes": "Served to guests with Omani coffee.",
        "dietary_tags": ["sweet", "festive", "traditional"],
    },
    {
        "id": "demo-mashuai",
        "name": "Mashuai",
        "name_ar": "مشوائي",
        "category": "Seafood",
        "region": "Coastal Oman",
        "description": "Roasted kingfish served with a tangy lemon rice preparation.",
        "ingredients_summary": "kingfish, rice, lemon, spices",
        "cooking_method": "Fish roasted and served with rice.",
        "cultural_notes": "A well-known coastal seafood preparation.",
        "dietary_tags": ["seafood", "high protein", "coastal"],
    },
    {
        "id": "demo-mishkak",
        "name": "Mishkak",
        "name_ar": "مشيكك",
        "category": "Meat",
        "region": "Muscat",
        "description": "Charcoal-grilled street skewers of marinated meat glazed with sour-spicy tamarind garlic sauce.",
        "ingredients_summary": "meat, garlic, tamarind, spices, peppers",
        "cooking_method": "Marinated and grilled over charcoal.",
        "cultural_notes": "A popular street-food favorite for casual gatherings.",
        "dietary_tags": ["grilled", "street food", "high protein"],
    },
    {
        "id": "demo-madrouba",
        "name": "Madrouba",
        "name_ar": "مدروبة",
        "category": "Rice",
        "region": "Across Oman",
        "description": "A savory beaten porridge of rice, tender shredded chicken, tomatoes, onions, and dried lime.",
        "ingredients_summary": "rice, chicken, tomatoes, onions, dried lime",
        "cooking_method": "Cooked until creamy and gently beaten for texture.",
        "cultural_notes": "Comforting and often shared during family meals.",
        "dietary_tags": ["comfort food", "family meal", "high protein"],
    },
    {
        "id": "demo-khubz-ragag",
        "name": "Khubz Ragag",
        "name_ar": "خبز رگّاق",
        "category": "Bread",
        "region": "Across Oman",
        "description": "Wafer-thin, crisp flatbread baked on a convex iron plate and served with savory or sweet toppings.",
        "ingredients_summary": "flour, water, yeast, cheese, honey",
        "cooking_method": "Baked on a hot convex pan until crisp and airy.",
        "cultural_notes": "A staple bread often eaten with breakfast spreads.",
        "dietary_tags": ["bread", "quick bite", "traditional"],
    },
    {
        "id": "demo-luqaimat",
        "name": "Omani Luqaimat",
        "name_ar": "لقيمات",
        "category": "Dessert",
        "region": "Across Oman",
        "description": "Crisp golden fried dumplings soaked in rich Omani date syrup and toasted sesame seeds.",
        "ingredients_summary": "flour, yeast, dates, sesame, oil",
        "cooking_method": "Fried until golden and drenched in date syrup.",
        "cultural_notes": "A celebratory sweet commonly served during Ramadan and gatherings.",
        "dietary_tags": ["sweet", "festive", "comfort food"],
    },
    {
        "id": "demo-marqooq",
        "name": "Omani Marqooq",
        "name_ar": "مرقوق",
        "category": "Stew",
        "region": "Interior Oman",
        "description": "Traditional savory stew prepared by cooking rolled dough discs directly in a spiced tomato broth.",
        "ingredients_summary": "dough, tomatoes, vegetables, spices, meat",
        "cooking_method": "Simmered until the dough discs soften in the spiced broth.",
        "cultural_notes": "A classic home-style dish known for its warm, hearty flavor.",
        "dietary_tags": ["hearty", "comfort food", "family meal"],
    },
]


def _demo_dishes(search: str | None = None, region: str | None = None, limit: int = 50):
    results = [dish.copy() for dish in DEMO_DISHES]
    if search:
        needle = search.lower()
        results = [
            dish
            for dish in results
            if needle in dish.get("name", "").lower()
            or needle in dish.get("description", "").lower()
            or needle in (dish.get("ingredients_summary") or "").lower()
        ]
    if region:
        region_value = region.lower()
        results = [dish for dish in results if region_value in (dish.get("region") or "").lower()]
    return results[:limit]


def _is_supabase_configured() -> bool:
    url = (settings.supabase_url or "").strip()
    anon = (settings.supabase_anon_key or "").strip()
    service = (settings.supabase_service_role_key or "").strip()
    placeholder_markers = (
        "your-project.supabase.co",
        "your_supabase_anon_key_here",
        "your_supabase_service_role_key_here",
        "example",
        "placeholder",
    )
    return bool(url and anon and service and not any(marker in url.lower() for marker in placeholder_markers) and not any(marker in anon.lower() for marker in placeholder_markers) and not any(marker in service.lower() for marker in placeholder_markers))


def list_dishes(search: str | None = None, region: str | None = None, limit: int = 50):
    if not _is_supabase_configured():
        return _demo_dishes(search, region, limit)
    try:
        q = get_admin_supabase().table("dishes").select("*").eq("is_published", True).limit(limit)
        if search:
            q = q.ilike("name", f"%{search}%")
        if region:
            q = q.ilike("region", f"%{region}%")
        return q.execute().data or []
    except Exception:
        return _demo_dishes(search, region, limit)


def get_dish(dish_id: str):
    if not _is_supabase_configured():
        for dish in _demo_dishes():
            if str(dish.get("id")) == str(dish_id):
                return dish
        return None
    try:
        result = get_admin_supabase().table("dishes").select("*, dish_ingredients(quantity, unit, ingredients(name, description)), nutrition(*)").eq("id", dish_id).maybe_single().execute()
        return result.data
    except Exception:
        for dish in _demo_dishes():
            if str(dish.get("id")) == str(dish_id):
                return dish
        return None


def find_matching_dish(name: str):
    rows = list_dishes(limit=200)
    normalized = name.lower().strip()
    for row in rows:
        if row["name"].lower() == normalized:
            return row
    for row in rows:
        if normalized in row["name"].lower() or row["name"].lower() in normalized:
            return row
    return None
