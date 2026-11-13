import base64
import json
import logging
from openai import OpenAI
from fastapi import HTTPException
from ..config import settings
from .food import list_dishes, find_matching_dish
from .classifier import classify_food_image

logger = logging.getLogger(__name__)

def client() -> OpenAI:
    if not settings.openai_api_key:
        raise HTTPException(status_code=503, detail="AI is not configured. Add OPENAI_API_KEY to backend/.env")
    return OpenAI(api_key=settings.openai_api_key)

def answer_food_question(message: str) -> str:
    dishes = list_dishes(limit=100)
    context = "\n".join([
        f"Dish: {d['name']}; region: {d.get('region')}; description: {d.get('description')}; ingredients: {d.get('ingredients_summary')}; preparation: {d.get('cooking_method')}; cultural notes: {d.get('cultural_notes')}"
        for d in dishes
    ])
    prompt = (
        "You are Oman Food AI, a warm and knowledgeable Omani culinary assistant. "
        "Answer using the curated dish data below. Be friendly, concise, and practical. "
        "If a dish is not clearly covered, say so instead of inventing details. "
        "For medical, allergy, or diet questions, recommend checking labels and consulting a qualified professional.\n\n"
        f"CURATED FOOD DATA:\n{context}\n\nUSER QUESTION: {message}\n\n"
        "Reply in a natural, conversational way. Prefer a short structured answer with: "
        "1) the main answer, 2) key ingredients or distinct traits, 3) cultural context or serving ideas when relevant."
    )

    try:
        response = client().chat.completions.create(
            model=settings.openai_chat_model,
            messages=[
                {"role": "system", "content": "You are a helpful Omani food guide. Give clear, culturally aware answers with practical detail and avoid guessing."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.35,
        )
        return response.choices[0].message.content or "I could not generate an answer. Please try again."
    except Exception as e:
        logger.warning("OpenAI chat completion failed: %s", e)
        lower_msg = message.lower()
        matched = []
        for d in dishes:
            if d['name'].lower() in lower_msg:
                matched.append(d)
            elif any(ing.strip().lower() in lower_msg for ing in (d.get('ingredients_summary') or '').split(',')):
                matched.append(d)
            elif any(term in lower_msg for term in ['shuwa', 'majboos', 'harees', 'halwa', 'luqaimat', 'mishkak', 'mashuai', 'madrouba', 'marqooq']):
                if any(term in lower_msg for term in [d['name'].lower()]):
                    matched.append(d)

        if matched:
            top = matched[0]
            return (
                f"Regarding {top['name']}: {top.get('description', '')}\n\n"
                f"Key ingredients: {top.get('ingredients_summary', 'N/A')}\n"
                f"Preparation: {top.get('cooking_method', 'N/A')}\n"
                f"Cultural note: {top.get('cultural_notes', 'A treasured Omani dish with rich heritage.') }"
            )

        return (
            "Oman Food AI knows about signature dishes like Shuwa, Majboos, Harees, Halwa, Mishkak, Luqaimat, and Mashuai. "
            "Ask me which dish suits a gathering, a dessert craving, or a protein-heavy meal and I’ll guide you."
        )

def recognize_food(image_bytes: bytes, mime_type: str) -> dict:
    """
    Recognizes Omani food in image bytes using the fine-tuned deep learning model,
    supplemented by database cross-referencing.
    """
    # 1. Primary engine: Fine-tuned PyTorch Computer Vision classifier
    try:
        data = classify_food_image(image_bytes)
    except Exception as e:
        logger.error("Local PyTorch classification failed: %s", e)
        data = {
            "dish_name": "Unknown dish",
            "confidence": "low",
            "confidence_score": 0.0,
            "description": "Recognition model could not classify image.",
            "likely_ingredients": [],
            "notes": str(e)
        }

    # 2. Match with Supabase database records
    data["matched_dish"] = find_matching_dish(data["dish_name"])

    # If database match exists, enrich with database details
    if data["matched_dish"]:
        matched = data["matched_dish"]
        if matched.get("description"):
            data["description"] = matched["description"]
        if matched.get("ingredients_summary"):
            data["likely_ingredients"] = [i.strip() for i in matched["ingredients_summary"].split(",")]

    return data
