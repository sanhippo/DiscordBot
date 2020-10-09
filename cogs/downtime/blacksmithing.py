from discord.ext import commands
import utils
import d20
import cogs.models.errors as error


# New - The Cog class must extend the commands.Cog class
class Blacksmithing(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # Define a Blacksmith Work
    @commands.command(
        name='blacksmithing',
        description='Handles all non assigned downtime things',
        aliases=['bs']
    )
    async def dt_blacksmith(self, ctx, hours: int, selection: int = None):

        try:
            playerdata = await utils.functions.getplayer(ctx)
        except error.NoNickFound as NoNickFound:
            await ctx.send(NoNickFound)
            return

        try:
            activitydata = await utils.functions.getactivity(ctx, ctx.command.name)
        except error.ActivityNotFound as ActivityNotFound:
            await ctx.send(ActivityNotFound)
            return

        result = d20.roll(activitydata.roll)
        desc = activitydata.results[result.total-1]["description"]

        pass


def setup(bot):
    bot.add_cog(Blacksmithing(bot))
    # Adds the Basic commands to the bot
    # Note: The "setup" function has to be there in every cog file