#https://github.com/LTMullineux/fastapi-snippets/blob/main/01-sqlalchemy-pydantic-crud-factory-pattern/snippets/crud.py

from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import delete, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas.schemas import BaseSchema

from .models.models import BaseModel

class ModelException(Exception):
    pass

class IntegrityConflictException(Exception):
    pass

class NotFoundException(Exception):
    pass

T = TypeVar('T', bound=BaseModel)

def CrudFactory(model: type[T]):
    class AsyncCrud[T]:

        @classmethod
        async def create_instance(
            cls,
            session,
            data: dict[str, Any],
            instantiate: bool = True,
        )  -> T:
            """
            Create an instance of a SQLModel using the provided data dictionary.

            This function dynamically maps nested dictionaries to corresponding ORM models.

            Args:
                model (Type[SQLModel]): The SQLModel class to instantiate.
                data (Dict[str, Any]): A dictionary containing the data to populate the model.

            Returns:
                SQLModel: An instance of the model populated with the provided data.

            Example:
                hero = create_instance(Hero, {"name": "Jason", "secret_name": "Tree"})
            """
            mapper = inspect(model)
            columns = {column.key: column for column in mapper.columns}
            relationships = {rel.key: rel for rel in mapper.relationships}

            instance_data = {}
            for key, value in (data or {}).items():
                if key in columns:
                    instance_data[key] = value
                elif key in relationships:
                    related_model = relationships[key].mapper.class_
                    RelatedCrud=CrudFactory(related_model)
                    if isinstance(value, list):
                        instance_data[key] = [
                            (await RelatedCrud.create_instance(session, v, False)) for v in value if v is not None
                        ]
                    elif value is not None:
                        instance_data[key] = await RelatedCrud.create_instance(session, value, False)
                    else:
                        instance_data[key] = [] if relationships[key].uselist else None

            db_model = model(**instance_data)
            if instantiate:
                try:
                    session.add(db_model)
                    await session.commit()
                    await session.refresh(db_model)
                    return db_model
                except IntegrityError:
                    raise IntegrityConflictException(
                        f"{model.__tablename__} conflicts with existing data.",
                    )
                except Exception as e:
                    raise ModelException(f"Unknown error occurred: {e}") from e
            return db_model

        @classmethod
        async def create(
            cls,
            session: AsyncSession,
            data: BaseSchema,
        ) -> T:
            """Accepts a Pydantic model, creates a new record in the database, catches
            any integrity errors, and returns the record.

            Args:
                session (AsyncSession): SQLAlchemy async session
                data (BaseSchema): Pydantic model

            Raises:
                IntegrityConflictException: if creation conflicts with existing data
                ModelException: if an unknown error occurs

            Returns:
                T: created SQLAlchemy model
            """
            try:
                db_model = model(**data.model_dump())
                session.add(db_model)
                await session.commit()
                await session.refresh(db_model)
                return db_model
            except IntegrityError:
                raise IntegrityConflictException(
                    f"{model.__tablename__} conflicts with existing data.",
                )
            except Exception as e:
                raise ModelException(f"Unknown error occurred: {e}") from e

        @classmethod
        async def create_many(
            cls,
            session: AsyncSession,
            data: list[BaseSchema],
            return_models: bool = False,
        ) -> list[T] | bool:
            """_summary_

            Args:
                session (AsyncSession): SQLAlchemy async session
                data (list[BaseSchema]): list of Pydantic models
                return_models (bool, optional): Should the created models be returned
                    or a boolean indicating they have been created. Defaults to False.

            Raises:
                IntegrityConflictException: if creation conflicts with existing data
                ModelException: if an unknown error occurs

            Returns:
                list[T] | bool: list of created SQLAlchemy models or boolean
            """
            db_models = [model(**d.model_dump()) for d in data]
            try:
                session.add_all(db_models)
                await session.commit()
            except IntegrityError:
                raise IntegrityConflictException(
                    f"{model.__tablename__} conflict with existing data.",
                )
            except Exception as e:
                raise ModelException(f"Unknown error occurred: {e}") from e

            if not return_models:
                return True

            for m in db_models:
                await session.refresh(m)

            return db_models

        @classmethod
        async def read(
            cls,
            session: AsyncSession,
            id_: str | UUID,
            column: str = "id",
            with_for_update: bool = False,
        ) -> T | None:
            """Fetches one record from the database based on a column value and returns
            it, or returns None if it does not exist. Raises an exception if the column
            doesn't exist.

            Args:
                session (AsyncSession): SQLAlchemy async session
                id_ (str | UUID): value to search for in `column`.
                column (str, optional): the column name in which to search.
                    Defaults to "id".
                with_for_update (bool, optional): Should the returned row be locked
                    during the lifetime of the current open transactions.
                    Defaults to False.

            Raises:
                ModelException: if the column does not exist on the model

            Returns:
                T: SQLAlchemy model or None
            """
            try:
                q = select(model).where(getattr(model, column) == id_)
            except AttributeError:
                raise ModelException(
                    f"Column {column} not found on {model.__tablename__}.",
                )

            if with_for_update:
                q = q.with_for_update()

            results = await session.execute(q)
            return results.unique().scalar_one_or_none()

        @classmethod
        async def read_many(
            cls,
            session: AsyncSession,
            ids: list[str | UUID] = None,
            offset: int = None,
            limit: int = None,
            column: str = "id",
            with_for_update: bool = False,
        ) -> tuple[list[T], int]:
            """Fetches multiple records from the database based on a column value and
            returns them with the number of rows. Raises an exception if the column doesn't exist.

            Args:
                session (AsyncSession): SQLAlchemy async session
                ids (list[str  |  UUID], optional): list of values to search for in
                    `column`. Defaults to None.
                column (str, optional): the column name in which to search
                    Defaults to "id".
                offset (int, optional): an integer OFFSET parameter, or a SQL
                    expression that provides an integer result. Defaults to None.
                limit (int, optional): an integer LIMIT parameter, or a SQL  
                    expression that provides an integer result. Defaults to None.
                with_for_update (bool, optional): Should the returned rows be locked
                    during the lifetime of the current open transactions.
                    Defaults to False.

            Raises:
                ModelException: if the column does not exist on the model

            Returns:
                list[T]: list of SQLAlchemy models
                int: amount of rows
            """
            q = (
                select(model)
                .offset(offset)
                .limit(limit)
            )
            if ids:
                try:
                    q = q.where(getattr(model, column).in_(ids))
                except AttributeError:
                    raise ModelException(
                        f"Column {column} not found on {model.__tablename__}.",
                    )

            if with_for_update:
                q = q.with_for_update()

            rows = await session.execute(q)
            data = rows.unique().scalars().all()
            return (data, len(data))

        @classmethod
        async def update(
            cls,
            session: AsyncSession,
            data: BaseSchema,
            id_: str | UUID,
            column: str = "id",
        ) -> T:
            """Updates a record in the database based on a column value and returns the
            updated record. Raises an exception if the record isn't found or if the
            column doesn't exist.

            Args:
                session (AsyncSession): SQLAlchemy async session
                data (BaseSchema): Pydantic schema for the updated data.
                id_ (str | UUID): value to search for in `column`
                column (str, optional): the column name in which to search
                    Defaults to "id".
            Raises:
                NotFoundException: if the record isn't found
                IntegrityConflictException: if the update conflicts with existing data

            Returns:
                T: updated SQLAlchemy model
            """
            db_model = await cls.read_one(
                session, id_, column=column, with_for_update=True
            )
            if not db_model:
                raise NotFoundException(
                    f"{model.__tablename__} {column}={id_} not found.",
                )

            values = data.model_dump(exclude_unset=True)
            for k, v in values.items():
                setattr(db_model, k, v)

            try:
                await session.commit()
                await session.refresh(db_model)
                return db_model
            except IntegrityError:
                raise IntegrityConflictException(
                    f"{model.__tablename__} {column}={id_} conflict with existing data.",
                )

        @classmethod
        async def update_many(
            cls,
            session: AsyncSession,
            updates: dict[str | UUID, BaseSchema],
            column: str = "id",
            return_models: bool = False,
        ) -> list[T] | bool:
            """Updates multiple records in the database based on a column value and
            returns the updated records. Raises an exception if the column doesn't
            exist.

            Args:
                session (AsyncSession): SQLAlchemy async session
                updates (dict[str  |  UUID, BaseSchema]): dictionary of id_ to
                    Pydantic update schema
                column (str, optional): the column name in which to search.
                    Defaults to "id".
                return_models (bool, optional): Should the created models be returned
                    or a boolean indicating they have been created. Defaults to False.
                    Defaults to False.

            Raises:
                IntegrityConflictException: if the update conflicts with existing data

            Returns:
                list[T] | bool: list of updated SQLAlchemy models or boolean
            """
            updates = {str(id): update for id, update in updates.items() if update}
            ids = list(updates.keys())
            db_models = await cls.read_many(
                session, ids=ids, column=column, with_for_update=True
            )

            for db_model in db_models:
                values = updates[str(getattr(db_model, column))].model_dump(
                    exclude_unset=True
                )
                for k, v in values.items():
                    setattr(db_model, k, v)
                session.add(db_model)

            try:
                await session.commit()
            except IntegrityError:
                raise IntegrityConflictException(
                    f"{model.__tablename__} conflict with existing data.",
                )

            if not return_models:
                return True

            for db_model in db_models:
                await session.refresh(db_model)

            return db_models

        @classmethod
        async def delete(
            cls,
            session: AsyncSession,
            id_: str | UUID,
            column: str = "id",
        ) -> int:
            """Removes a record from the database based on a column value. Raises an
            exception if the column doesn't exist.

            Args:
                session (AsyncSession): SQLAlchemy async session
                id (str | UUID): value to search for in `column` and delete
                column (str, optional): the column name in which to search.
                    Defaults to "id".

            Raises:
                ModelException: if the column does not exist on the model

            Returns:
                int: number of rows removed, 1 if successful, 0 if not. Can be greater
                    than 1 if id_ is not unique in the column.
            """
            try:
                query = delete(model).where(getattr(model, column) == id_)
            except AttributeError:
                raise ModelException(
                    f"Column {column} not found on {model.__tablename__}.",
                )

            rows = await session.execute(query)
            await session.commit()
            return rows.rowcount

        @classmethod
        async def delete_many(
            cls,
            session: AsyncSession,
            ids: list[str | UUID],
            column: str = "id",
        ) -> int:
            """Removes multiple records from the database based on a column value.
            Raises an exception if the column doesn't exist.

            Args:
                session (AsyncSession): SQLAlchemy async session
                ids (list[str  |  UUID]): list of values to search for in `column` and
                column (str, optional): the column name in which to search.
                    Defaults to "id".

            Raises:
                ModelException: if ids is empty to stop deleting an entire table
                ModelException: if column does not exist on the model

            Returns:
                int: _description_
            """
            if not ids:
                raise ModelException("No ids provided.")

            try:
                query = delete(model).where(getattr(model, column).in_(ids))
            except AttributeError:
                raise ModelException(
                    f"Column {column} not found on {model.__tablename__}.",
                )

            rows = await session.execute(query)
            await session.commit()
            return rows.rowcount

    return AsyncCrud[T]

