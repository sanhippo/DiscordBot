import asyncio
import faulthandler
import logging
import sys
import traceback

import random
import discord
import gspread
import asyncio

import credentials
import math
import datetime
import functions

from discord.errors import Forbidden, HTTPException, InvalidArgument, NotFound
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError


Testing = credentials.Testing


if Testing == 0:
    token = credentials.BotToken  # Actual Token
else:
    token = credentials.TestToken  # Test Token


def get_prefix(client, message):

    prefixes = ['$']    # sets the prefixes, u can keep it as an array of only 1 item if you need only one prefix

    if not message.guild:
        prefixes = ['$']   # Only allow '==' as a prefix when in DMs, this is optional

    # Allow users to @mention the bot instead of using a prefix when using a command. Also optional
    # Do `return prefixes` if u don't want to allow mentions instead of prefix.
    return commands.when_mentioned_or(*prefixes)(client, message)


bot = commands.Bot(                         # Create a new bot
    command_prefix=get_prefix,              # Set the prefix
    description='A bot used for tutorial',  # Set a description for the bot
    owner_id=146431797016657920,            # Your unique User ID
    case_insensitive=True                   # Make the commands case insensitive
)

cogs = ['cogs.basic', 'cogs.embed']


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    bot.remove_command('help')
    # Removes the help command
    # Make sure to do this before loading the cogs
    for cog in cogs:
        bot.load_extension(cog)
    return


# Finally, login the bot
bot.run(token, bot=True, reconnect=True)

