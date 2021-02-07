from discord.ext import commands
import utils
import d20
import cogs.models.errors as error


# New - The Cog class must extend the commands.Cog class
class Guarding(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # Define a Blacksmith Work
    @commands.command(
        name='guard_manage',
        description='Handles all non assigned downtime things',
        aliases=['gnpc']
    )
    async def dt_guard_manage(self, ctx):



        pass


def setup(bot):
    bot.add_cog(Guarding(bot))
    # Adds the Basic commands to the bot
    # Note: The "setup" function has to be there in every cog file