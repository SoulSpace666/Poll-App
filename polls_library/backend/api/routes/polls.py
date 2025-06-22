from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from ...config import settings
from ...crud import CrudFactory
from ...models.models import PollModel
from ...schemas.schemas import (
    PollCreateSchema,
    PollExtendedSchema,
    PollPublicSchema,
    PollsPublicSchema
)
from ..deps import SessionDep, CurrentSuperuser

router = APIRouter(prefix="/polls", tags=["polls"])

PollCrud = CrudFactory(PollModel)

@router.get("/", response_model=PollsPublicSchema)
async def read_polls(
    session: SessionDep, offset: int = 0
):
    #Retrieve polls
    data, count = await PollCrud.read_many(session,offset=offset, limit=offset+settings.BACKEND_PAGINATION_AMOUNT)
    return PollsPublicSchema(
        data=data,
        count=count
    )


@router.get("/{id}", response_model=PollPublicSchema)
async def read_poll(
    session: SessionDep, id: int
):
    #Get poll by ID
    poll = await PollCrud.read(session, id)
    if poll is None:
        return PlainTextResponse(None, 204)
    return poll


@router.post("/", response_model=PollPublicSchema)
async def create_poll(
    *, session: SessionDep, current_user: CurrentSuperuser, poll_in: PollCreateSchema
):
    #Create new poll
    poll_processed = PollExtendedSchema(
        **(poll_in.model_dump() |
            {
                "author_id":current_user.id
            }  
        ))
    poll = await PollCrud.create_instance(session, poll_processed.model_dump())
    return poll


@router.delete("/{id}")
async def delete_poll(
    session: SessionDep, current_user: CurrentSuperuser, id: int
):
    #Delete a poll
    if ( await PollCrud.delete(session,id) ) == 1:
        return PlainTextResponse(None, 200)
    else:
        return PlainTextResponse(None, 204)