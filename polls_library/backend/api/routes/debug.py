from fastapi import APIRouter, Request
from starlette.routing import Route

from ..deps import CurrentUser, SessionDep
from ...schemas.schemas import UserSchema
router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/cusr", response_model=UserSchema)
async def read_current_user(
    session: SessionDep, current_user: CurrentUser
):
    #Check current user

    return current_user

@router.get("/routes")
async def read_app_routes(request: Request):
    #Check current user
    
    routes : list[Route] = request.app.routes
    return list(map(str, routes))
