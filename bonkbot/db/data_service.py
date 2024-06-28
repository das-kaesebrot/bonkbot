from sqlalchemy import URL, create_engine, Engine, select
from sqlalchemy.orm import Session

from ..models.models import User, Guild


class DataService:
    __engine: Engine = None
    __session = None

    def __init__(self, *, connection_string: str | URL = "sqlite://") -> None:
        self.__engine = create_engine(connection_string, echo=True)
        Base.metadata.create_all(self.__engine)        
        self.__session = Session(self.__engine)
        
    def __del__(self):
        self.__session.close()
        

    def get_user(self, user_id: int) -> User:
        """Gets a user by the specified user_id. Always returns a value, either an existing user or a new one generated on the fly.

        Args:
            user_id (int): the user id

        Returns:
            User: the user that was found or just added to the database
        """
        with self.__session.begin() as session:
            select_statement = select(User).where(User.id.is_(user_id))

            user = session.scalars(select_statement).one_or_none()

            if user:
                return user
            
            # if no user was found, generate one
            new_user = User(id=user_id, bonks=0, guilds=[])
            session.add(new_user)
            return new_user
        
    def get_guild(self, guild_id: int) -> Guild:
        """Gets a guild (server) by the specified guild_id. Always returns a value, either an existing guild or a new one generated on the fly.

        Args:
            guild_id (int): the guild id

        Returns:
            Guild: the guild that was found or just added to the database
        """
        with self.__session.begin() as session:
            select_statement = select(Guild).where(Guild.id.is_(guild_id))

            guild = session.scalars(select_statement).one_or_none()

            if guild:
                return guild
            
            # if no guild was found, generate one
            new_guild = Guild(id=guild, prefix="!", users=[])
            session.add(new_guild)
            return new_guild