# bonkbot

This is a meme bot for bonking users in discord.

![Horny jail meme](assets/bonk.png)

## What it does
The bot allows you to bonk users behaving horny in chat.
If someone has been bonked more than 10 times, they get sent to horny jail (-> a role is assigned) for a specified time, by default 600 seconds.
For ways to customize all these values, please see `!bonkhelp` or the usage section.

## Invite to your server
Feel free to invite the bot using this [invite link](https://discord.com/oauth2/authorize?client_id=1254550959510519869).

**In the beginning, everyone is allowed to send admin commands. Be sure to set the admin role with the command `!bonkadmin [role mention]` as soon as possible!**

## Usage

### Unprivileged user commands
| Command | Description |
| - | - |
| `!bonk` as a reply to a message | Bonk the author of the original message (`!` can be ommitted) |
| `!bonk [name \| tagged user]` | Bonk a user (`!` can be ommitted) |
| `!bonks` | Get the top 5 most bonked users |
| `!bonks [name \| tagged user]` | Get the bonks of a user |
| `!bonkprefix` | Get the prefix for this bot's commands
| `!bonkhelp` | Show help message |

### Admin commands
| Command | Description |
| - | - |
| `!bonkpardon [name \| tagged user]` | Pardon a user from horny jail |
| `!hornyjail` as a reply to a message | Send the author of the original message to horny jail immediately |
| `!hornyjail [name \| tagged user]` | Send a user to horny jail immediately |
| `!bonkadmin` | Get the role that is assigned as admin role |
| `!bonkadmin [role mention]` | Set the admin role |
| `!bonkjail` | Get the role that is assigned as horny jail |
| `!bonkjail [role mention]` | Set the horny jail role |
| `!bonkjailtime`| Get the horny jail time (in seconds) |
| `!bonkjailtime [jail seconds]` | Set the horny jail time (in seconds) |
| `!bonkjailamount` | Get the bonks needed to send a user to horny jail |
| `!bonkjailamount [jail bonks]` | Set the bonks needed to send a user to horny jail |
| `!bonkprefix [prefix]` | Set the prefix for this bot's commands |
| `!bonkprefix reset` | Reset the prefix back to `!` |

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
            "horny_jail_seconds": 600,
            "force_override": true
        }
    }
}
```

## Open Source License Attribution

This application uses Open Source components. You can find the source code of their open source projects along with license information below. We acknowledge and are grateful to these developers for their contributions to open source.
### [discord.py](https://github.com/Rapptz/discord.py)
- Copyright (c) 2015-present [Rapptz](https://github.com/Rapptz)
- [MIT License](https://github.com/Rapptz/discord.py/blob/master/LICENSE)

### [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy)
- Copyright (c) 2005-present [SQLAlchemy authors and contributors](https://github.com/sqlalchemy/sqlalchemy/blob/main/AUTHORS)
- [MIT License](https://github.com/sqlalchemy/sqlalchemy/blob/main/LICENSE)

### [pydantic-settings](https://github.com/pydantic/pydantic-settings)
- Copyright (c) 2022-present [Samuel Colvin](https://github.com/samuelcolvin) and [other contributors](https://github.com/pydantic/pydantic-settings/graphs/contributors)
- [MIT License](https://github.com/pydantic/pydantic-settings/blob/main/LICENSE)

### [Flake8](https://github.com/PyCQA/flake8)
- Copyright (c) 2011-2013 Tarek Ziade <tarek@ziade.org>
- Copyright (c) 2012-2016 Ian Cordasco <graffatcolmingov@gmail.com>
- [Flake8 license (MIT)](https://github.com/PyCQA/flake8/blob/main/LICENSE)

### [pytest](https://github.com/pytest-dev/pytest)
- Copyright (c) 2004-present [Holger Krekel](https://github.com/hpk42) and [other contributers](https://github.com/pytest-dev/pytest/blob/main/AUTHORS)
- [MIT License](https://github.com/pytest-dev/pytest/blob/main/LICENSE)