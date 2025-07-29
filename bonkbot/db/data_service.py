from datetime import datetime
import logging
import discord
from sqlalchemy import URL, and_, create_engine, Engine, delete, desc, func, select
from sqlalchemy.orm import Session, aliased

from ..models.models import Base, Bonk, User, Guild

class DataService:
    __engine: Engine = None
    __session = None
    _logger: logging.Logger

    def __init__(self, *, connection_string: str | URL = "sqlite://") -> None:
        self._logger = logging.getLogger(__name__)
        self._logger.info(f"Creating database engine with connection string '{connection_string}'")
        
        # only echo SQL statements if we're logging at the debug level
        echo = self._logger.getEffectiveLevel() <= logging.DEBUG
        
        self.__engine = create_engine(connection_string, echo=echo)
        Base.metadata.create_all(self.__engine)
        self.__session = Session(self.__engine)
        
        assert self.__engine is not None
        assert self.__session is not None

    def __del__(self):
        self._logger.info("Shutting down")
        self.__session.close()

    def get_user(self, discord_id: int, guild_id: int) -> User:
        """Gets a user by the specified user_id. Always returns a value, either an existing user or a new one generated on the fly.

        Args:
            discord_id (int): the discord user id
            guild_id (int): the guild id

        Returns:
            User: the user that was found or just added to the database
        """
        
        user_id = User.get_id(discord_id, guild_id)

        select_statement = select(User).where(User.id.is_(user_id))

        user = self.__session.scalars(select_statement).one_or_none()

        if user:
            return user

        # if no user was found, generate one
        new_user = User(id=user_id, discord_id=discord_id)
        guild = self.get_guild(guild_id)
        guild.users.append(new_user)
        self.__session.add_all([new_user, guild])

        return new_user
    
    def get_guild_prefix(self, guild: int | discord.guild.Guild) -> str:
        guild_id = 0
        if isinstance(guild, discord.guild.Guild):
            guild_id = guild.id
        else:
            guild_id = guild

        select_statement = select(Guild.prefix).where(Guild.id.is_(guild_id))

        prefix = self.__session.scalars(select_statement).one_or_none()

        if prefix:
            return prefix
        
        new_guild = self.get_guild(guild)
        return new_guild.prefix
    

    def get_guild(self, guild: int | discord.guild.Guild) -> Guild:
        """Gets a guild (server) by the specified guild_id. Always returns a value, either an existing guild or a new one generated on the fly.

        Args:
            guild (int | discord.guild.Guild): the guild object or id

        Returns:
            Guild: the guild that was found or just added to the database
        """
        guild_id = 0
        if isinstance(guild, discord.guild.Guild):
            guild_id = guild.id
        else:
            guild_id = guild

        select_statement = select(Guild).where(Guild.id.is_(guild_id))

        guild = self.__session.scalars(select_statement).one_or_none()

        if guild:
            return guild

        # if no guild was found, generate one
        new_guild = Guild(id=guild_id, prefix="!", users=[])
        self.__session.add(new_guild)

        return new_guild

    def get_top_bonked_users(self, guild_id: int, limit: int = 5):
        bonk_alias = aliased(Bonk)
        bonk_count_subquery = (
            select(
                bonk_alias.user,
                func.count(bonk_alias.id).label('bonk_count')
            )
            .group_by(bonk_alias.user)
            .subquery()
        )
            
        select_statement = (
            select(User)
            .join(bonk_count_subquery, User.id == bonk_count_subquery.c.user)
            .where(User.guild == guild_id)
            .order_by(desc(bonk_count_subquery.c.bonk_count))
            .limit(limit)
        )
        top_users = self.__session.scalars(select_statement).all()

        return top_users

    def save_and_commit(self, object):
        self.__session.add(object)
        self.__session.commit()
        self.__session.flush()
        
    def get_all_pending_jail_releases(self) -> list[User]:
        """Returns all users that should be released from horny jail.
        This is determined based on the current timestamp and the user's `horny_jail_until` prop.
        If the current time is later than the user's prop, jail time is over.
        If the horny_jail_until prop is `None` (NULL), a user is considered free.

        Returns:
            list[User]: The free users
        """
        now = datetime.now()
        
        select_statement = select(User).where(and_(User.horny_jail_until, User.horny_jail_until < now))
        free_users = self.__session.scalars(select_statement).all()
        return free_users
    
    def set_users_free(self, users: list[User]):
        """Set the horny jail prop to NULL in the database so that the user is considered free again.

        Args:
            users (list[User]): A list of users to set free
        """
        changed_users = []
        
        for user in users:
            user.horny_jail_until = None
            changed_users.append(user)
            
        self.__session.add_all(changed_users)
        self.__session.commit()
        self.__session.flush()
    
    def get_total_bonk_count(self):
        select_statement = select(func.count()).select_from(Bonk)
        return self.__session.execute(select_statement).scalar() or 0
    
    def get_total_users_in_horny_jail_count(self):
        select_statement = select(func.count()).select_from(User).where(User.horny_jail_until)
        return self.__session.execute(select_statement).scalar() or 0
    
    def get_total_guild_count(self):
        select_statement = select(func.count()).select_from(Guild)
        return self.__session.execute(select_statement).scalar() or 0
    
    def get_all_guild_ids(self) -> list[int]:
        select_statement = select(Guild.id)
        return self.__session.scalars(select_statement).all()
    
    def delete_guilds(self, guild_ids: list):
        delete_statement = delete(Guild).where(Guild.id.in_(guild_ids))
        self.__session.execute(delete_statement)
        self.__session.commit()
        self.__session.flush()
        