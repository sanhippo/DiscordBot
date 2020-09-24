import asyncio
import faulthandler
import logging
import sys
import traceback

import discord
from discord.errors import Forbidden, HTTPException, InvalidArgument, NotFound
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError
import credentials


def get_prefix(client, message):

    prefixes = ['$']    # sets the prefixes, u can keep it as an array of only 1 item if you need only one prefix

    # Allow users to @mention the bot instead of using a prefix when using a command. Also optional
    # Do `return prefixes` if u don't want to allow mentions instead of prefix.
    return commands.when_mentioned_or(*prefixes)(client, message)


bot = commands.Bot(                         # Create a new bot
    command_prefix=get_prefix,              # Set the prefix
    description='Downtime Bot',  # Set a description for the bot
    owner_id=146431797016657920,            # Your unique User ID
    case_insensitive=True                   # Make the commands case insensitive
)

testing = credentials.testing

if testing == 0:
    token = credentials.bottoken  # Actual Token
else:
    token = credentials.testtoken  # Test Token


# case_insensitive=True is used as the commands are case sensitive by default

cogs = ['cogs.basic']

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    for cog in cogs:
        bot.load_extension(cog)
    return

# Finally, login the bot
bot.run(token, bot=True, reconnect=True)
