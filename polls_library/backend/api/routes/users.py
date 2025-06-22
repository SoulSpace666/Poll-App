
from fastapi import APIRouter

from ..deps import (
    CurrentUser,
)

from ...schemas.schemas import VotesPublicSchema


router = APIRouter(prefix="/users", tags=["users"])

@router.get("/votes", response_model=VotesPublicSchema)
def read_user_votes(current_user: CurrentUser):
    data = current_user.votes
    return VotesPublicSchema(
        data=data,
        count=len(data)
    )
