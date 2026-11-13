from fastapi import APIRouter
from ..dependencies import OptionalUser
from ..schemas import ChatRequest
from ..services.ai import answer_food_question
from ..supabase_client import get_admin_supabase
router = APIRouter(prefix="/assistant", tags=["AI Assistant"])

@router.post("/chat")
def chat(payload: ChatRequest, user: OptionalUser = None):
    answer = answer_food_question(payload.message)
    if user and user.get("id"):
        try:
            get_admin_supabase().table("chat_history").insert({"user_id": user["id"], "question": payload.message, "answer": answer}).execute()
        except Exception:
            pass
    return {"answer": answer}
