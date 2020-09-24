from discord.ext import commands
from datetime import datetime as d


# New - The Cog class must extend the commands.Cog class
class Basic(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # Define a new command
    @commands.command(
        name='ping',
        description='The ping command',
        aliases=['p']
    )
    async def ping_command(self, ctx):
        start = d.timestamp(d.now())
        # Gets the timestamp when the command was used

        msg = await ctx.send(content='Pinging')
        # Sends a message to the user in the channel the message with the command was received.
        # Notifies the user that pinging has started

        await msg.edit(content=f'Pong!\nOne message round-trip took {(d.timestamp(d.now()) - start) * 1000}ms.')
        # Ping completed and round-trip duration show in ms
        # Since it takes a while to send the messages
        # it will calculate how much time it takes to edit an message.
        # It depends usually on your internet connection speed
        return

    @commands.command(
        name='say',
        description='The say command',
        aliases=['repeat', 'parrot'],
        usage='<text>'
    )
    async def say_command(self, ctx):
        # The 'usage' only needs to show the parameters
        # As the rest of the format is generated automatically

        # Lets see what the parameters are: -
        # The self is just a regular reference to the class
        # ctx - is the Context related to the command
        # For more reference - https://discordpy.readthedocs.io/en/rewrite/ext/commands/api.html#context

        # Next we get the message with the command in it.
        msg = ctx.message.content

        # Extracting the text sent by the user
        # ctx.invoked_with gives the alias used
        # ctx.prefix gives the prefix used while invoking the command
        prefix_used = ctx.prefix
        alias_used = ctx.invoked_with
        text = msg[len(prefix_used) + len(alias_used):]

        # Next, we check if the user actually passed some text
        if text == '':
            # User didn't specify the text

            await ctx.send(content='You need to specify the text!')

            pass
        else:
            # User specified the text.

            await ctx.send(content=f"**{text}**")

            pass

        return


def setup(bot):
    bot.add_cog(Basic(bot))
    # Adds the Basic commands to the bot
    # Note: The "setup" function has to be there in every cog file