from fastapi import APIRouter, HTTPException
from ..schemas import SignupRequest, LoginRequest
from ..supabase_client import get_public_supabase
from ..dependencies import CurrentUser

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup")
def signup(payload: SignupRequest):
    try:
        result = get_public_supabase().auth.sign_up({"email": payload.email, "password": payload.password})
        return {"user": result.user.model_dump() if result.user else None, "session": result.session.model_dump() if result.session else None, "message": "Check your email if email confirmation is enabled."}
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Signup failed. Check credentials and Supabase Auth settings.") from exc

@router.post("/login")
def login(payload: LoginRequest):
    try:
        result = get_public_supabase().auth.sign_in_with_password({"email": payload.email, "password": payload.password})
        return {"user": result.user.model_dump() if result.user else None, "session": result.session.model_dump() if result.session else None}
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid email or password") from exc

@router.get("/me")
def me(user: CurrentUser):
    return user
