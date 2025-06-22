from sqlalchemy.engine import Engine
from .database import get_db_connection
from .config import settings
from sqlalchemy import event


async def init_db() -> None:
    '''    
    Tables should be created with Alembic migrations
    But if you don't want to use migrations, create
    the tables un-commenting the next lines.
    '''
    if settings.DEBUG_USE_SQLITE:
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        from .models import models
        async with get_db_connection() as connection:
            await connection.run_sync(models.BaseModel.metadata.create_all)