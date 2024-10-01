import pytest
from bonkbot.db.data_service import DataService

@pytest.fixture
def dataservice_instance():
    service = DataService()
    return service

def test_get_user_should_return(dataservice_instance):
    discord_id = 1
    guild_id = 1
    
    user = dataservice_instance.get_user(discord_id, guild_id)
    assert user is not None
    assert user.discord_id == discord_id
    