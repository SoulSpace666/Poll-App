from datetime import datetime, timedelta, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, conlist

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UUIDMixinSchema(BaseSchema):
    id: UUID | None

class EmailMixinSchema(BaseSchema):
    id: EmailStr | None = Field(default=None, max_length=255)

class IntMixinSchema(BaseSchema):
    id: int | None = Field(default=None)


class UserBaseSchema(BaseSchema):
    is_superuser: bool | None = False
    active: bool | None = True


class UserSchema(UserBaseSchema, EmailMixinSchema):
    polls: list["PollPublicSchema"]
    votes: list["VotePublicSchema"]


class UserPublicSchema(UserBaseSchema, EmailMixinSchema):
    pass


class UserCreateSchema(UserBaseSchema):
    pass


class UsersPublicSchema(BaseSchema):
    data: list["UserPublicSchema"]
    count: int


class PollBaseSchema(BaseSchema):
    title: str
    description: str | None = None
    multiple_choice: bool | None = False
    anonymous: bool | None = False
    expires_at: datetime | None = None

class PollExtendedSchema(PollBaseSchema):
    author_id: EmailStr
    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=3)
    )
    options: list["OptionBaseSchema"] = conlist("OptionBaseSchema", min_length=1)

class PollPublicSchema(PollExtendedSchema, IntMixinSchema):
    options: list["OptionPublicSchema"] = conlist("OptionBaseSchema", min_length=1)

class PollCreateSchema(PollBaseSchema):
    options: list["OptionCreateSchema"] = conlist("OptionBaseSchema", min_length=1)

class PollsPublicSchema(BaseSchema):
    data: list[PollPublicSchema]
    count: int


class OptionBaseSchema(BaseSchema):
    title: str

class OptionPublicSchema(OptionBaseSchema, UUIDMixinSchema):
    pass

class OptionCreateSchema(OptionBaseSchema):
    pass




class VoteBaseSchema(BaseSchema):
    poll_id: int

class VotePublicSchema(VoteBaseSchema, UUIDMixinSchema):
    voter_id: EmailStr
    selected_options: list["OptionPublicSchema"] = conlist("OptionBaseSchema", min_length=1)

class VoteCreateSchema(VoteBaseSchema):
    selected_options: list["UUID"] = conlist("OptionBaseSchema", min_length=1)

class VotesPublicSchema(BaseSchema):
    data: list[VotePublicSchema]
    count: int