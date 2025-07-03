from uuid import UUID
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from datetime import datetime, timezone

from ...crud import CrudFactory
from ..deps import CurrentUser, SessionDep
from ...models.models import (
    OptionModel,
    PollModel,
    UserModel,
    VoteModel,
)
from ...schemas.schemas import (
    VoteCreateSchema,
    VotePublicSchema,
    VotesPublicSchema
)

router = APIRouter(prefix="/votes", tags=["votes"])

PollCrud = CrudFactory(PollModel)
OptionCrud = CrudFactory(OptionModel)
VoteCrud = CrudFactory(VoteModel)
UserCrud = CrudFactory(UserModel)

@router.get("/polls/{poll_id}", response_model=VotesPublicSchema)
async def read_votes_by_poll(
    session: SessionDep,
    current_user: CurrentUser,
    poll_id: int,
    offset: int = 0,
):
    #Retrieve votes of a poll (by poll_id)

    #checking for an anonymous survey
    if not current_user.is_superuser:
        poll = await PollCrud.read(session, poll_id)
        if poll.anonymous:
            return HTTPException(403, "This poll is anonymous")
        
    data, count = await VoteCrud.read_many(session, [poll_id], column="poll_id")
    return VotesPublicSchema(
        data=data,
        count=count
    )

@router.get("/{id}", response_model=VotePublicSchema)
async def read_vote(
    session: SessionDep, 
    id: UUID
):
    #Get vote by ID
    vote = await VoteCrud.read(session, id)
    if vote is None:
        return PlainTextResponse(None, 204)
    
    #check if it's an anonymous poll
    poll = await PollCrud.read(session, vote.poll_id)
    if poll is None:
        return PlainTextResponse(None, 204) 
    if poll.anonymous:
        raise HTTPException(403, "This vote was taken for an anonymous poll")
    
    return vote

@router.delete("/{id}")
async def delete_vote(
    session: SessionDep, 
    current_user: CurrentUser, id: UUID
):
    #Delete a vote
    if ( await VoteCrud.delete(session,id) ) == 1:
        return PlainTextResponse(None, 200)
    else:
        return PlainTextResponse(None, 204)


@router.post("/", response_model=VotePublicSchema, name="create_vote_api")
async def create_vote(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    vote_in: VoteCreateSchema,
):
    #Create new vote

    #checking for an existing voice
    await session.refresh(current_user)
    existing_vote= [vote for vote in current_user.votes if vote.poll_id==vote_in.poll_id]
    if existing_vote:
        raise HTTPException(status_code=400, detail="Already voted in this poll")

    #checking for the existence of options
    options, count = await OptionCrud.read_many(session, vote_in.selected_options)
    if count!=len(vote_in.selected_options):
        raise HTTPException(status_code=404, detail="One or multiple options voted for are not found")
    
    #checking for a survey with multiple responses
    if count>1 and not (await PollCrud.read(session, vote_in.poll_id)).multiple_choice:
        raise HTTPException(status_code=400, detail="This poll is not multiple choice")

    #сhecking the validity period
    poll = await PollCrud.read(session, vote_in.poll_id)
    if poll.expires_at and poll.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Voting for this poll has closed")

    vote = await VoteCrud.create_instance(
        session,
        vote_in.model_dump(exclude="selected_options") | {"voter_id": current_user.id},
        False,
    )

    vote.selected_options = options
    session.add(vote)
    await session.commit()
    await session.refresh(vote)
    return vote