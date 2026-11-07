from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.attempts import router as attempts_router
from app.api.auth import router as auth_router
from app.api.concepts import router as concepts_router
from app.api.courses import router as courses_router
from app.api.dashboard import router as dashboard_router
from app.api.documents import router as documents_router
from app.api.exams import router as exams_router
from app.api.progress import router as progress_router
from app.api.roadmaps import router as roadmaps_router
from app.api.sessions import router as sessions_router

app = FastAPI(title="StudyMate API")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|172\.\d+\.\d+\.\d+)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Support both root and /api prefixes
api_router = APIRouter(prefix="/api")

routers = [
    auth_router,
    courses_router,
    documents_router,
    concepts_router,
    sessions_router,
    attempts_router,
    roadmaps_router,
    exams_router,
    progress_router,
    dashboard_router,
]

for router in routers:
    app.include_router(router)
    api_router.include_router(router)

app.include_router(api_router)


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok"}
