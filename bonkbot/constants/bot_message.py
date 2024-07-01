class BotMessage():
    BONK = "**🔨 bonk {name}**\n\n_User has been bonked {amount} times so far_"
    SENT_TO_JAIL = "🚨 WEE WOO 🚨\n**{name}** just got sent to horny jail until <t:{timestamp}>"
    
    GUILD_PREFIX_INFO = "Guild is using prefix `{}`"
    GUILD_PREFIX_SET = "Set guild command prefix to `{}`"
    
    USER_BONKS_INFO = "User **{name}** has been bonked {amount} times so far"
    
    HELP = """**Available commands**

`{prefix}bonk` as a reply to a message - Bonk the author of the original message (`{prefix}` can be ommitted)
`{prefix}bonk [name | tagged user]` - Bonk a user (`{prefix}` can be ommitted)
`{prefix}bonks` - Get the top 5 most bonked users
`{prefix}bonks [name | tagged user]` - Get the bonks of a user

`{prefix}bonkprefix`- Get the prefix for this bot's commands
`{prefix}bonkprefix [prefix]` - Set the prefix for this bot's commands
`{prefix}bonkprefix reset` - Reset the prefix back to `!`

`{prefix}bonkhelp` - Show this help message
"""