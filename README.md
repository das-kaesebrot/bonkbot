# bonkbot

This is a meme bot for bonking users in discord.

![Horny jail meme](assets/bonk.png)

## Usage

Feel free to invite the bot  this [invite link](https://discord.com/oauth2/authorize?client_id=1254550959510519869).

| Command | Description |
| - | - |
| `!bonk` as a reply to a message | Bonk the author of the original message (`!` can be ommitted) |
| `!bonk [name \| tagged user]` | Bonk a user (`!` can be ommitted) |
| `!bonks` | Get the top 5 most bonked users |
| `!bonks [name \| tagged user]` | Get the bonks of a user |
| `!bonkpardon [name \| tagged user]` | Pardon a user from horny jail | 
| `!bonkprefix` | Get the prefix for this bot's commands
| `!bonkprefix [prefix]` | Set the prefix for this bot's commands |
| `!bonkprefix reset` | Reset the prefix back to `!` |
| `!bonkhelp` | Show this help message |

## Configuration

You may configure the bot via multiple sources.
Environment variables take precedence over the config file.

### Environment variables
| Variable name | Description | Default value | Required? |
| - | - | - | - |
| `BONKBOT_TOKEN` | Bot token to use for login at the discord API | `None` | Yes |
| `BONKBOT_LOG_LEVEL` | Logging level | `info` | No |
| `BONKBOT_DB_CONNECTION_STRING` | The connection string for the database engine to use | `sqlite://` | No |

### Config file
The file has to be called `config.json` and has to be mounted next to the script at `/usr/local/bin/bonkbot/config.json`.
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
