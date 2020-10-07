from discord.ext import commands
import utils
from datetime import datetime as d


# New - The Cog class must extend the commands.Cog class
class Downtime(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # Define a new command
    @commands.command(
        name='other',
        description='Handles all non assigned downtime things'
    )
    async def dt_other(self, ctx, hours: int, selection: int = None):
        start = d.timestamp(d.now())
        # Gets the timestamp when the command was used

        if selection is None:
            test1 = ("Hey", 1)
            test2 = ("Hoe", 2)
            test4 = ("Heyhoe", 3)
            test3 = [test1, test2, test4]
            candy = await utils.functions.get_selection(ctx, test3)
            print(candy)




        msg = await ctx.send(content='Pinging')
        # Sends a message to the user in the channel the message with the command was received.
        # Notifies the user that pinging has started

        await msg.edit(content=f'Pong!\nOne message round-trip took {(d.timestamp(d.now()) - start) * 1000}ms.')
        # Ping completed and round-trip duration show in ms
        # Since it takes a while to send the messages
        # it will calculate how much time it takes to edit an message.
        # It depends usually on your internet connection speed
        return


def setup(bot):
    bot.add_cog(Downtime(bot))
    # Adds the Basic commands to the bot
    # Note: The "setup" function has to be there in every cog file