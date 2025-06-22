from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.requests import Request
from sqlalchemy.orm import Session

from ..exceptions import UserMissingException

from ..database import get_db_session
from ..models.models import UserModel

SessionDep = Annotated[Session, Depends(get_db_session)]

def get_current_user_on_client(request: Request):
    return request.session.get("user")


async def get_current_user_in_db(session: SessionDep, request: Request):
    user_on_client = get_current_user_on_client(request)
    if user_on_client:
        user_in_db = await session.get(UserModel, user_on_client.get("email"))
        if not user_in_db:
            raise HTTPException(status_code=400, detail="Possible forged session cookie, user not found")
        if not user_in_db.active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return user_in_db
    else:
        raise UserMissingException(403,'no user in session')

CurrentUser = Annotated[UserModel, Depends(get_current_user_in_db)]

def get_current_active_superuser(request: Request, current_user: CurrentUser) -> UserModel:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user

CurrentSuperuser = Annotated[UserModel, Depends(get_current_active_superuser)]
