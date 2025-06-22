#https://blog.authlib.org/2020/fastapi-google-login

from fastapi import APIRouter
from authlib.integrations.starlette_client import OAuth, OAuthError
import json
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from ..deps import SessionDep
from ...config import settings
from ...models.models import UserModel

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"


oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url=GOOGLE_DISCOVERY_URL,
    # for including refresh token
    refresh_token_url="https://oauth2.googleapis.com/token",
    authorize_params= {'access_type': 'offline'},
    client_kwargs={
        "scope": "openid email profile",
        # 'prompt': 'select_account',  # force to select account
    },
)

google_router = APIRouter(tags=["google"])

@google_router.get("/")
async def homepage(request: Request):
    user = request.session.get("user")
    html = ''
    if user:
        if settings.DEBUG:
            data = json.dumps(user)
            html+= f'<pre>{data}</pre>'
        html+= f'<a href="{settings.API_V1_STR}/logout">logout</a>'
    else: 
        html+= f'<a href="{settings.API_V1_STR}/login">login</a>'
    return HTMLResponse(html)

#this opens google auth page
@google_router.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth")
    return await oauth.google.authorize_redirect(request, redirect_uri)

#this is where user is redirected to after /login
@google_router.get("/auth")
async def auth(request: Request, session: SessionDep):
    async def _fetch_user_id() -> str:
        try:
            token = await oauth.google.authorize_access_token(request)
        except OAuthError as error:
            return HTMLResponse(f"<h1>{error}</h1>")
        user = token.get("userinfo")
        if user:
            request.session["user"] = dict(user)
        return request.session.get("user").get("email")

    async def _select_or_create_user(user_id : str) -> UserModel:
        statement = select(UserModel).where(UserModel.id == user_id)
        user = (await session.scalars(statement)).first()
        if not user:
            user = UserModel(id=user_id)
        return user

    user_id = await _fetch_user_id()
    user = await _select_or_create_user(user_id)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return RedirectResponse(url=settings.API_V1_STR+"/")


@google_router.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url=settings.API_V1_STR+"/")

if settings.DEBUG_AUTHLIB_LOG:
    import logging
    import sys
    log = logging.getLogger('authlib')
    log.addHandler(logging.StreamHandler(sys.stdout))
    log.setLevel(logging.CRITICAL)