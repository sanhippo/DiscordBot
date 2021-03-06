from discord.ext import commands
import credentials
from utils import functions
import old


def get_prefix(client, message):

    prefixes = ['$']    # sets the prefixes, u can keep it as an array of only 1 item if you need only one prefix

    # Allow users to @mention the bot instead of using a prefix when using a command. Also optional
    # Do `return prefixes` if u don't want to allow mentions instead of prefix.
    return commands.when_mentioned_or(*prefixes)(client, message)


Testing = credentials.Testing

if Testing == 0:
    token = credentials.BotToken  # Actual Token
else:
    token = credentials.TestToken  # Test Token


bot = commands.Bot(                         # Create a new bot
    command_prefix=get_prefix,              # Set the prefix
    description='Downtime Bot',             # Set a description for the bot
    owner_id=146431797016657920,            # Your unique User ID
    case_insensitive=True                   # Make the commands case insensitive
)

# case_insensitive=True is used as the commands are case sensitive by default

cogs = ['cogs.basic', 'cogs.embed']

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    for cog in cogs:
        bot.load_extension(cog)
    return


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    ctx = await bot.get_context(message)
    messagesplit = ctx.message.content.split(" ")
    cmdlower = messagesplit[0].lower()
    ctx.message.content = ctx.message.content.replace(messagesplit[0], cmdlower)

    if ctx.command is not None:
        await bot.invoke(ctx)
        return

    await old.do_on_message(ctx.message, bot)

    return


# Finally, login the bot
bot.run(token, bot=True, reconnect=True)
