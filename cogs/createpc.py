from discord.ext import commands
from datetime import datetime as d
import d20
from utils.functions import try_delete


# New - The Cog class must extend the commands.Cog class
class CreatePC(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # Define a new command
    @commands.command(
        name='createpc',
        description='Create a New Player Character',
        aliases=['pc']
    )
    async def createpc_command(self, ctx):

        await ctx.send(content="Starting Character Creation")

        # Check to see if player has a character to make
            #if not leave setup and alarm with no character avaliable to be created

        # Check to see if players has a character in creation already
            #if they determine where they left off and jump to that step.

        # Ask If they want to roll for stats or use the heroic array. Let them know rolled stats can't be moved.
             #Rolled Stats = 6 4d6kh3

        roll_str = d20.roll("4d6kh3")
        roll_dex = d20.roll("4d6kh3")
        roll_con = d20.roll("4d6kh3")
        roll_int = d20.roll("4d6kh3")
        roll_wis = d20.roll("4d6kh3")
        roll_cha = d20.roll("4d6kh3")

        # Display Rolls
        sent_rolls = await ctx.send(f"**Str:** {roll_str}\n**Dex:** {roll_dex}\n**Con:** {roll_con}\n**Int:** {roll_int}\n**Wis:** {roll_wis}\n**Cha:** {roll_cha}")

        print(sent_rolls.id)

        emoji_reroll = '<:ReRoll:806548887753457708>' #Reroll Icon
        emoji_accept = '\N{THUMBS UP SIGN}' #Accept Emoji


        await sent_rolls.add_reaction(emoji_reroll)
        await sent_rolls.add_reaction(emoji_accept)

        def check(reaction, user):
            return user == ctx.author

        try:
            reaction = await self.bot.wait_for('reaction_add', timeout=10.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("Timeout Waiting for Selection, Please use .pc to resume in the future.")
        else:
            if reaction == emoji_accept:
                await ctx.send("You Accepted The Rolls")
            elif reaction == emoji_reroll:
                await ctx.send("You Rerolled your stats")
            else:
                await ctx.send("You can't add your own reactions")


        await try_delete(sent_rolls)

                # Give Option to Reroll
                    #Take Rolled Stats
                    #Use Lesser Heroic Array
                #Take Rolled Stats
                #Take Lesser Heroic Array

            #If Heroic Array Picked Let player assign rolls
                #Strength score
                #Dexterity Score
                #Constitution Score
                #Intelligence Score
                #Wisdom Score
                #Charisma Score

            #Give Option to restart assigning process if heroic picked

        #Ask Character To Pick Race.
            #Pick Subclass if any.
            # Assign Score improvements

        #Ask Character To Pick Class
            #Ask Character To Pick Subclass

        #Ask Character To Pick Background

        #Finialize character creation

        #Mention to character they should level up, and check out the store for prices.

        return


def setup(bot):
    bot.add_cog(CreatePC(bot))
    # Adds the Basic commands to the bot
    # Note: The "setup" function has to be there in every cog file