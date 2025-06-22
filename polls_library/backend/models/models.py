from datetime import datetime, timedelta, timezone
from uuid import uuid4

from pydantic import EmailStr
from sqlalchemy import ForeignKey, String
from uuid import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

class BaseModel(DeclarativeBase, AsyncAttrs):
    pass

class UserModel(BaseModel):
    __tablename__ = 'users'  # Specify the table name

    id: Mapped[EmailStr] = mapped_column(String(length=255), primary_key=True, nullable=True)  # EmailStr can be represented as String
    is_superuser: Mapped[bool] = mapped_column(default=False)
    active: Mapped[bool] = mapped_column(default=True)


    # Relationships
    polls: Mapped[list["PollModel"]] = relationship(back_populates="author", lazy="selectin", cascade="all, delete, delete-orphan") #?do we delete polls when user is deleted or not
    votes: Mapped[list["VoteModel"]] = relationship(back_populates="voter", lazy="selectin", cascade="all, delete, delete-orphan")


class PollModel(BaseModel):
    __tablename__ = 'polls'  # Specify the table name

    id: Mapped[int] = mapped_column(primary_key=True, nullable=True)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    multiple_choice: Mapped[bool] = mapped_column(default=False)
    anonymous: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc) + timedelta(hours=3))
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
    
    # author & author_id are '| None' for allowing user.polls=None
    author_id: Mapped[EmailStr | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # Foreign key to User
    author: Mapped["UserModel | None"] = relationship(back_populates="polls", lazy="selectin")
    options: Mapped[list["OptionModel"]] = relationship(back_populates="poll", cascade="all, delete, delete-orphan", lazy="selectin")
    votes: Mapped[list["VoteModel"]] = relationship(back_populates="poll", cascade="all, delete, delete-orphan")

class VoteOptionLinksModel(BaseModel):
    __tablename__ = 'vote_option_links'  # Specify the table name

    vote_id: Mapped[UUID] = mapped_column(ForeignKey("votes.id", ondelete="CASCADE"), primary_key=True)
    option_id: Mapped[UUID] = mapped_column(ForeignKey("options.id", ondelete="CASCADE"), primary_key=True)


class OptionModel(BaseModel):
    __tablename__ = 'options'  # Specify the table name

    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False)
    poll_id: Mapped[int] = mapped_column(ForeignKey("polls.id", ondelete="CASCADE"), nullable=False)  # Foreign key to Poll
    poll: Mapped["PollModel"] = relationship(back_populates="options", lazy="selectin")
    votes: Mapped[list["VoteModel"]] = relationship(secondary="vote_option_links", back_populates="selected_options", lazy="selectin", cascade="all, delete")


class VoteModel(BaseModel):
    __tablename__ = 'votes'  # Specify the table name

    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)

    # voter & voter_id are '| None' for allowing user.votes=None
    voter_id: Mapped[EmailStr | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  #? should we delete all votes of a deleted user
    voter: Mapped["UserModel | None"] = relationship(back_populates="votes", lazy="selectin")
    poll_id: Mapped[int] = mapped_column(ForeignKey("polls.id", ondelete="CASCADE"), nullable=False)
    poll: Mapped["PollModel"] = relationship(back_populates="votes", lazy="selectin", passive_deletes=True)
    selected_options: Mapped[list["OptionModel"]] = relationship(secondary="vote_option_links", back_populates="votes", lazy="selectin",passive_deletes=True)