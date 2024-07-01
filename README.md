# bonkbot

## Example config

Environment variables:
- `BONKBOT_TOKEN` - the Discord token to use


`config.json`
```json
{
    "log_level": "info",
    "db_connection_string": "sqlite:///data.db",
    "guild_config": {
        "YOUR_GUILD_ID": {
            "admin_role": 13774555512916872331,
            "horny_jail_role": 1377464510916872449,
            "horny_jail_bonks": 10,
            "horny_jail_seconds": 600
        }
    }
}
```