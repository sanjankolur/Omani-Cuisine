from typing import Annotated, Optional
from fastapi import Depends, Header, HTTPException, status
from .supabase_client import get_public_supabase

async def get_current_user(authorization: Annotated[str | None, Header()] = None) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer access token required")
    token = authorization.split(" ", 1)[1].strip()
    try:
        result = get_public_supabase().auth.get_user(token)
        user = result.user
        if not user:
            raise ValueError("No user in token response")
        return {"id": str(user.id), "email": user.email}
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired access token") from exc

async def get_optional_user(authorization: Annotated[str | None, Header()] = None) -> Optional[dict]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    try:
        result = get_public_supabase().auth.get_user(token)
        user = result.user
        if not user:
            return None
        return {"id": str(user.id), "email": user.email}
    except Exception:
        return None

CurrentUser = Annotated[dict, Depends(get_current_user)]
OptionalUser = Annotated[Optional[dict], Depends(get_optional_user)]
