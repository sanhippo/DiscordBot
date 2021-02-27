from discord.errors import Forbidden, HTTPException, InvalidArgument, NotFound
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError
import credentials
from utils import functions


global datalogdelay
datalogdealy = False
global shorttermdata
shorttermdata = []


def get_prefix(client, message):

    prefixes = ['.']    # sets the prefixes, u can keep it as an array of only 1 item if you need only one prefix

    # Allow users to @mention the bot instead of using a prefix when using a command. Also optional
    # Do `return prefixes` if u don't want to allow mentions instead of prefix.
    return commands.when_mentioned_or(*prefixes)(client, message)


bot = commands.Bot(                         # Create a new bot
    command_prefix=get_prefix,              # Set the prefix
    description='Desolation Bot',             # Set a description for the bot
    owner_id=146431797016657920,            # Your unique User ID
    case_insensitive=True                   # Make the commands case insensitive
)

testing = credentials.testing

if testing == 0:
    token = credentials.bottoken  # Actual Token
else:
    token = credentials.testtoken  # Test Token


# case_insensitive=True is used as the commands are case sensitive by default

cogs = ['cogs.basic', 'cogs.embed', 'cogs.dice', 'cogs.playercharacter', 'cogs.session']

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    for cog in cogs:
        bot.load_extension(cog)
    return

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

    elif isinstance(error, (commands.UserInputError, commands.NoPrivateMessage, ValueError)):
        return await ctx.send(
            f"Error: {str(error)}\nUse `{ctx.prefix}help " + ctx.command.qualified_name + "` for help.")

    elif isinstance(error, commands.CheckFailure):
        msg = str(error) or "You are not allowed to run this command."
        return await ctx.send(f"Error: {msg}")

    elif isinstance(error, commands.CommandOnCooldown):
        return await ctx.send("This command is on cooldown for {:.1f} seconds.".format(error.retry_after))

    elif isinstance(error, commands.MaxConcurrencyReached):
        return await ctx.send(f"Only {error.number} instance{'s' if error.number > 1 else ''} of this command per "
                              f"{error.per.name} can be running at a time.")

    elif isinstance(error, CommandInvokeError):
        original = error.original
        if isinstance(original, Forbidden):
            try:
                return await ctx.author.send(
                    f"Error: I am missing permissions to run this command. "
                    f"Please make sure I have permission to send messages to <#{ctx.channel.id}>."
                )
            except HTTPException:
                try:
                    return await ctx.send(f"Error: I cannot send messages to this user.")
                except HTTPException:
                    return

        elif isinstance(original, NotFound):
            return await ctx.send("Error: I tried to edit or delete a message that no longer exists.")

        elif isinstance(original, HTTPException):
            if original.response.status == 400:
                return await ctx.send(f"Error: Message is too long, malformed, or empty.\n{original.text}")
            elif 499 < original.response.status < 600:
                return await ctx.send("Error: Internal server error on Discord's end. Please try again.")



@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.type.name == "private":
        return

    ctx = await bot.get_context(message)
    messagesplit = ctx.message.content.split(" ")
    cmdlower = messagesplit[0].lower()
    ctx.message.content = ctx.message.content.replace(messagesplit[0], cmdlower)

    if ctx.channel.category.name == "in-character":
        global datalogdealy
        global shorttermdata
        if datalogdealy is False:
            shorttermdata = []
            shorttermdata.append({"id": ctx.author.id, "count": len(ctx.message.content)})
            datalogdealy = True
            await functions.waittime(300)
            functions.update_rp_data(shorttermdata)
            datalogdealy = False

        else:
            for record in shorttermdata:
                if record["id"] == ctx.author.id:
                    record["count"] = record["count"] + len(ctx.message.content)
                    break
            if record["id"] != ctx.author.id:
                shorttermdata.append({"id": ctx.author.id, "count": len(ctx.message.content)})
            print("Heyo")

    if ctx.command is not None:
        await bot.invoke(ctx)
        return

    # await old.do_on_message(ctx.message, bot)




# Finally, login the bot
bot.run(token, bot=True, reconnect=True)