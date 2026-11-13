from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import auth, dishes, assistant, recognition, nutrition, recommendations, analytics

app = FastAPI(title=settings.app_name, version="1.0.0", description="AI-driven food intelligence for Omani cuisine")
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
for router in [auth.router, dishes.router, assistant.router, recognition.router, nutrition.router, recommendations.router, analytics.router]:
    app.include_router(router, prefix=settings.api_v1_prefix)

@app.get("/")
def root():
    return {"name": settings.app_name, "status": "running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}
