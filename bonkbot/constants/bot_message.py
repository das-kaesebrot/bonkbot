class BotMessage():
    BONK = "**🔨 bonk {name}**\n\n_User has been bonked {amount} times so far_"
    SENT_TO_JAIL = "🚨 WEE WOO 🚨\n**{name}** just got sent to horny jail until <t:{timestamp}>"
    PARDONED = "🕊 User **{}** was released early from horny jail for good behaviour"
    
    GUILD_PREFIX_INFO = "Guild is using prefix `{}`"
    GUILD_PREFIX_SET = "Set guild command prefix to `{}`"
    
    JAIL_ROLE_INFO = "Guild is using horny jail role <@&{}>"
    JAIL_ROLE_SET = "Set guild horny jail role to <@&{}>"
    
    ADMIN_ROLE_INFO = "Guild is using admin role <@&{}>"
    ADMIN_ROLE_SET = "Set guild admin role to <@&{}>"
    
    JAIL_TIME_INFO = "Guild is using {} seconds jail time"
    JAIL_TIME_SET = "Set guild jail time to {} seconds"
    
    JAIL_BONKS_INFO = "Guild is using {} bonks to send to horny jail"
    JAIL_BONKS_SET = "Set horny jail bonks to {}"
    
    USER_BONKS_INFO = "User **{name}** has been bonked {amount} times so far"
    
    HELP = """**Available commands**

**User commands**
`{prefix}bonk` as a reply to a message - Bonk the author of the original message (`{prefix}` can be ommitted)
`{prefix}bonk [name | tagged user]` - Bonk a user (`{prefix}` can be ommitted)
`{prefix}bonks` - Get the top 5 most bonked users
`{prefix}bonks [name | tagged user]` - Get the bonks of a user

`{prefix}bonkprefix` - Get the prefix for this bot's commands

`{prefix}bonkhelp` - Show this help message

**Admin commands**
`{prefix}bonkpardon [name | tagged user]` - Pardon a user from horny jail
`{prefix}hornyjail` as a reply to a message - Send the author of the original message to horny jail immediately
`{prefix}hornyjail [name | tagged user]` - Send a user to horny jail immediately

`{prefix}bonkadmin` - Get the role that is assigned as admin role
`{prefix}bonkadmin [role mention]` - Set the admin role

`{prefix}bonkjail` - Get the role that is assigned as horny jail
`{prefix}bonkjail [role mention]` - Set the horny jail role

`{prefix}bonkjailtime` - Get the horny jail time (in seconds)
`{prefix}bonkjailtime [jail seconds]` - Set the horny jail time (in seconds)

`{prefix}bonkjailamount` - Get the bonks needed to send a user to horny jail
`{prefix}bonkjailamount [jail bonks]` - Set the bonks needed to send a user to horny jail

`{prefix}bonkprefix [prefix]` - Set the prefix for this bot's commands
`{prefix}bonkprefix reset` - Reset the prefix back to `!`
"""