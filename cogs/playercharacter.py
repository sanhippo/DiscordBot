from discord.ext import commands
from datetime import datetime as d
import d20
import gspread
from utils.functions import try_delete, getinput, confirm, search, search_and_select

gc = gspread.service_account()

workbook = gc.open("Desolation Player Management")
sheet_managment = workbook.worksheet("Management")
sheet_characters = workbook.worksheet("Character")

emoji_reroll = '<:ReRoll:806548887753457708>'  # Reroll Icon
emoji_accept = '\N{THUMBS UP SIGN}'  # Accept Emoji


# New - The Cog class must extend the commands.Cog class
class playercharacter(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # Define a new command
    @commands.command(
        name='playercharacter',
        description='Create a New Player Character, or check existing character',
        aliases=['pc']
    )
    async def PCCommand(self, ctx, *, character: str = None):

        batch_character_data = sheet_characters.get_all_records()

        if character is not None:

            results = None
            try:
                results = await search_and_select(ctx, batch_character_data, character, lambda batch_character_data: batch_character_data["Name"])
            finally:
                if results is None:  # Exit if no matching character name is found
                    return
                print(str(results.DiscordID))

        try:  # See if the user has a character
            get_character = sheet_characters.findall(str(ctx.author.id), in_column=2)
        finally:
            if len(get_character) == 0:  # Player Needs to Create a Character
                # The Player Needs To Create A Character
                name = await getinput(ctx, "What Is your Characters Name?")

                if name is None:
                    await ctx.send("Timeout. Try .PC in the future to continue.")
                    return
                else:
                    # Add check to see if they accepted or not. If Accepted Continue.
                    await confirm(ctx, f"Confirm The Name: {name}")
                    cstep = 100
                    characterdata = [str(name), str(ctx.author.id), cstep]
                    sheet_characters.append_row(characterdata, value_input_option='USER_ENTERED',
                                               insert_data_option="INSERT_ROWS",
                                               table_range="A1")
            else:  # If the user has at least one character either created or already existing
                print("Hey hoe")




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



        await sent_rolls.add_reaction(emoji_reroll)
        await sent_rolls.add_reaction(emoji_accept)

        def check(reaction, user):
            if user == ctx.author:
                return reaction

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=10.0, check=check)
        except asyncio.TimeoutError:

            await ctx.send("Timeout Waiting for Selection, Please use .pc to resume in the future.")
        else:

            if reaction.emoji == '👍':

                await ctx.send("You Accepted The Rolls")
            elif str(reaction.emoji) == "<:ReRoll:806548887753457708>":

                await ctx.send("You Accepted The Rolls2")
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
    bot.add_cog(playercharacter(bot))
    # Adds the Basic commands to the bot
    # Note: The "setup" function has to be there in every cog file