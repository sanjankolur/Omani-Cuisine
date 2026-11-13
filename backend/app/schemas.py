from pydantic import BaseModel, Field
from typing import Any

class SignupRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)

class LoginRequest(BaseModel):
    email: str
    password: str

class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=4000)

class RecommendationRequest(BaseModel):
    dietary_preferences: list[str] = []
    avoid_ingredients: list[str] = []
    goal: str | None = None
    limit: int = Field(default=5, ge=1, le=20)

class RecognitionResponse(BaseModel):
    dish_name: str
    confidence: str
    description: str
    likely_ingredients: list[str]
    notes: str
    matched_dish: dict[str, Any] | None = None
    image_url: str | None = None
