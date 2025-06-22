from fastapi import APIRouter

from ..config import settings
from .routes import google, polls, votes, users

api_router = APIRouter()


api_router.include_router(google.google_router)
api_router.include_router(polls.router)
api_router.include_router(votes.router)
api_router.include_router(users.router)

if settings.DEBUG:
    from .routes import debug
    api_router.include_router(debug.router)