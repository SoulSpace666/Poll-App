from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ..config import settings
from ..api.deps import CurrentUser, SessionDep
from ..models.models import PollModel, VoteModel

def base_context(request: Request):
    return {"PROJECT_NAME": settings.PROJECT_NAME}

templates = Jinja2Templates(directory="backend/frontend/templates", context_processors=[base_context])
frontend_router = APIRouter(prefix="/frontend", tags=["frontend"])

@frontend_router.get("/new-poll", name="frontend_create_poll")
async def create_poll(request: Request, current_user: CurrentUser):
    return templates.TemplateResponse(
        request=request,
        name="create_poll.jinja2",
        context={
            "API_CALL_STR": f"{settings.API_V1_STR}/polls/",
            "current_user": current_user,
        }
    )

@frontend_router.get("/polls/", name="frontend_read_polls")
async def read_polls_redirect(request: Request, current_user: CurrentUser, page: int = 1):
    return RedirectResponse(request.url_for("frontend_read_polls_with_page", page=1))

@frontend_router.get("/polls/{page}", name="frontend_read_polls_with_page")
async def read_polls(
    request: Request,
    current_user: CurrentUser,
    db: SessionDep,
    page: int = 1
):
    total_polls = await db.scalar(select(func.count(PollModel.id)))
    
    if total_polls == 0:
        max_page = 1
    else:
        max_page = (total_polls + settings.BACKEND_PAGINATION_AMOUNT - 1) // settings.BACKEND_PAGINATION_AMOUNT
    
    if page < 1:
        page = 1
    elif page > max_page:
        page = max_page
    
    offset = (page - 1) * settings.BACKEND_PAGINATION_AMOUNT
    
    polls_query = (
        select(PollModel)
        .options(selectinload(PollModel.options))
        .offset(offset)
        .limit(settings.BACKEND_PAGINATION_AMOUNT)
    )
    
    polls_result = await db.execute(polls_query)
    polls = polls_result.scalars().all()
    
    user_votes = {}
    if current_user:
        votes_query = (
            select(VoteModel)
            .filter(VoteModel.voter_id == current_user.id)
            .options(selectinload(VoteModel.selected_options))
        )
        votes_result = await db.execute(votes_query)
        user_votes_list = votes_result.scalars().all()
        
        for vote in user_votes_list:
            options_dict = {option.id: option.title for option in vote.selected_options}
            user_votes[vote.poll_id] = options_dict
    
    return templates.TemplateResponse(
        request=request,
        name="polls.jinja2",
        context={
            "current_user": current_user,
            "page": page,
            "polls": polls,
            "polls_count": total_polls,
            "user_votes": user_votes,
            "user_votes_count": len(user_votes),
            "max_page": max_page
        },
    )

@frontend_router.get("/vote-success", name="vote_success")
async def vote_success(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="vote_success.jinja2",
        context={}
    )