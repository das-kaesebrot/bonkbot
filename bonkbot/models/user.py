from typing import List
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    bonks: Mapped[int] = mapped_column()
    guilds: Mapped[List["Guild"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

class Guild(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    prefix: Mapped[str] = mapped_column(String(1))
    users: Mapped["User"] = relationship(back_populates="guild")
    