from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.career_assistant import router as career_assistant_router
from app.api.routes.health import router as health_router
from app.api.routes.job_matches import router as job_matches_router
from app.api.routes.interviews import router as interviews_router
from app.api.routes.resumes import router as resumes_router
from app.api.routes.resume_analyses import router as resume_analyses_router
from app.api.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(analytics_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(resumes_router)
api_router.include_router(resume_analyses_router)
api_router.include_router(job_matches_router)
api_router.include_router(career_assistant_router)
api_router.include_router(interviews_router)
