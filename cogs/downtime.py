from discord.ext import commands
import utils
from datetime import datetime as d
import gspread
import asyncio
import d20



gc = gspread.service_account()

workbook = gc.open("Elantris Downtime")
sheetstatus = workbook.worksheet("Status")
sheetplayer = workbook.worksheet("Player")


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
        # Gets the timestamp when the command was used

        if selection is None:
            choices = []
            get_values = sheetstatus.batch_get(["L:M"], major_dimension="Columns")
            row = 1
            arraypointer = 0

            for row in range(len(get_values[0][1])):
                if get_values[0][0][row] == "1":
                    choices.append((get_values[0][1][row], arraypointer))
                    arraypointer += 1
                row += 1

            candy = await utils.functions.get_selection(ctx, choices)
            await ctx.send(choices[candy][0])

        return

    # Define a Blacksmith Work
    @commands.command(
        name='blacksmiting',
        description='Handles all non assigned downtime things',
        aliases=['bs']
    )
    async def dt_blacksmith(self, ctx, hours: int, selection: int = None):

        playerdata = await utils.functions.getplayer(ctx)

        if playerdata is None:
            await ctx.send(f"Error: User {ctx.author.nick} not found.")
            return

        activitydata = await utils.functions.getactivity(ctx, ctx.command.name)

        if activitydata is None:
            await ctx.send(f"Error: Activity {ctx.command.name} not found.")
            return


def setup(bot):
    bot.add_cog(Downtime(bot))
    # Adds the Basic commands to the bot
    # Note: The "setup" function has to be there in every cog file