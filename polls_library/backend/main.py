import contextlib
from fastapi import FastAPI, Request

from .init_db import init_db
from .config import settings
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from .api.main import api_router
from .exceptions import UserMissingException
from .frontend.test import frontend_router

def init_middleware(app: FastAPI):
    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY, max_age=settings.MAX_SESSION_AGE)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.HTTPS:
        from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
        app.add_middleware(HTTPSRedirectMiddleware)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)


init_middleware(app)

@app.exception_handler(UserMissingException)
async def requires_login(request: Request, _: Exception):
    return RedirectResponse(request.url_for("login"))

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(frontend_router)

if settings.DEBUG_REDIRECT_APIV1:
    from fastapi.responses import RedirectResponse # noqa: E402
    @app.get("/")
    def homepage():
        return RedirectResponse(settings.API_V1_STR+"/")


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=settings.BACKEND_HOST, port=settings.BACKEND_PORT)
