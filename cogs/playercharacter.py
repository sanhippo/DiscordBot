from discord.ext import commands
from datetime import datetime as d
import d20
import gspread
from utils.functions import try_delete, getinput, confirm, search, search_and_select, update_character_data
from gspread.models import Cell

gc = gspread.service_account()

workbook = gc.open("Desolation Player Management")
sheet_managment = workbook.worksheet("Management")
sheet_characters = workbook.worksheet("Character")

emoji_reroll = '<:ReRoll:806548887753457708>'  # Reroll Icon
emoji_accept = '\N{THUMBS UP SIGN}'  # Accept Emoji
emoji_statarray = '<:Flameicon:811997280516309123>'

strcolum = "D"
chacolum = "I"


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
                #  Display Character Information
                # TODO: Add code to display Character Information
                return

        # See if the user has a character # Todo: Needs to be improved to not be so slow try a search and select
        rowfound = 2
        for character_data in batch_character_data:
            if str(character_data["DiscordID"]) == str(ctx.author.id):
                break
            else:
                character_data = None
                rowfound += 1
        if character_data is None:
            x = 0
            while x == 0:
                name = await getinput(ctx, "What Is your Characters Name?")

                if name is None:  # Timeout waiting for user to enter a name.
                    await ctx.send("Timeout. Try .PC in the future to continue.")
                    return

                #  TODO: Change Code to Update File Instead of making new ones
                confirmation = await confirm(ctx, f"Confirm The Name: {name}", delete_msgs=True)

                if confirmation is None:
                    await ctx.send("Timeout. Try .PC in the future to continue.")
                    return
                elif confirmation:
                    x = 1
                    character_data = {
                        "Name": str(name),
                        "DiscordID": str(ctx.author.id),
                        "Step": 100
                    }
                    sheetdata = [character_data["Name"], character_data["DiscordID"], character_data["Step"]]
                    sheet_characters.append_row(sheetdata, value_input_option='USER_ENTERED',
                                            insert_data_option="INSERT_ROWS",
                                            table_range="A1")

        # Roll for Stats
        while character_data["Step"] < 200:
            if (character_data["Step"] == 100) or (character_data["Step"] == 150):  # Roll for Stats
                roll_str = d20.roll("4d6kh3")
                roll_dex = d20.roll("4d6kh3")
                roll_con = d20.roll("4d6kh3")
                roll_int = d20.roll("4d6kh3")
                roll_wis = d20.roll("4d6kh3")
                roll_cha = d20.roll("4d6kh3")
            else:  # Resume checking for Stats
                roll_str = character_data["Str"]
                roll_dex = character_data["Dex"]
                roll_con = character_data["Con"]
                roll_int = character_data["Int"]
                roll_wis = character_data["Wis"]
                roll_cha = character_data["Cha"]

            # Display Rolls
            sent_rolls = await ctx.send(f"**Str:** {roll_str}\n**Dex:** {roll_dex}\n**Con:** {roll_con}\n**Int:** {roll_int}\n**Wis:** {roll_wis}\n**Cha:** {roll_cha}")

            if character_data["Step"] == 100:  # Rolling for the First Time
                await sent_rolls.add_reaction(emoji_reroll)

            await sent_rolls.add_reaction(emoji_accept)
            await sent_rolls.add_reaction(emoji_statarray)

            def check(reaction, user):
                if user == ctx.author:
                    return reaction

            reaction = None
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=5.0, check=check)
            finally:
                if reaction is None:
                    if (character_data["Step"] == 100) or (character_data["Step"] == 150):

                        # Convert Rolls To Storage
                        character_data["Str"] = roll_str.total
                        character_data["Dex"] = roll_dex.total
                        character_data["Con"] = roll_con.total
                        character_data["Int"] = roll_int.total
                        character_data["Wis"] = roll_wis.total
                        character_data["Cha"] = roll_cha.total

                        # Update So On Resume It Does Not roll again
                        if character_data["Step"] == 100:
                            character_data["Step"] = 125
                        else:
                            character_data["Step"] = 175

                        update_character_data(character_data, rowfound)

                    await ctx.send("Timeout Waiting for Selection, Please use .pc to resume in the future.")
                else:

                    if reaction.emoji == '👍':

                        character_data["Step"] = 300

                    elif str(reaction.emoji) == emoji_reroll:
                        if character_data["Step"] == 100:
                            character_data["Step"] = 150

                    elif str(reaction.emoji) == emoji_statarray:
                        character_data["Step"] = 200

                    else:
                        await ctx.send("You can't add your own reactions. Aborting, Please use .pc to resume in the future.")

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

        # Manually Assign Stats
        while 200 <= character_data["Step"] < 300:
            if character_data["Step"] == 200:
                character_data["Str"] = 0
                character_data["Dex"] = 0
                character_data["Con"] = 0
                character_data["Int"] = 0
                character_data["Wis"] = 0
                character_data["Cha"] = 0
                character_data["Step"] = 210

            Statarray = (16, 14, 13, 12, 11, 8, 7)
            if character_data["Step"] == 210:
                x = 0

            if character_data["Step"] == 220:
                x = 1

            if character_data["Step"] == 230:
                x = 2

            if character_data["Step"] == 240:
                x = 3

            if character_data["Step"] == 250:
                x = 4

            if character_data["Step"] == 260:
                x = 5

            if character_data["Step"] < 270:
                sentassignment = await ctx.send(f"Assign {Statarray[x]}: ")
                if character_data["Str"] == 0:
                    await sentassignment.add_reaction(emoji_str)

                if character_data["Dex"] == 0:
                    await sentassignment.add_reaction(emoji_dex)

                if character_data["Con"] == 0:
                    await sentassignment.add_reaction(emoji_con)

                if character_data["Int"] == 0:
                    await sentassignment.add_reaction(emoji_int)

                if character_data["Wis"] == 0:
                    await sentassignment.add_reaction(emoji_wis)

                if character_data["Cha"] == 0:
                    await sentassignment.add_reaction(emoji_cha)

            await sentassignment.add_reaction(emoji_reroll)

            if character_data["Step"] == 270:
                await sentassignment.add_reaction(emoji_accept)















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