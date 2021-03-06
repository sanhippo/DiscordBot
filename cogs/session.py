import gspread
from utils.functions import checkperm, get_emoji, try_delete, utc_to_local, emojiconfirm, sendlong, emojimulti, \
	search_dictionary, getinput, RepresentsInt, get_cell_for_update, get_dictionary_key, logger
import asyncio
from discord.ext import commands
from credentials import testing
import datetime
from cogs.playercharacter import sheet_characters

gc = gspread.service_account()
workbook = gc.open("Desolation - Session Join Request")
sheet_activesession = workbook.worksheet("ActiveSessions")
sheet_signups = workbook.worksheet("signups")
sheet_joinlist = workbook.worksheet("JoinList")
workbook2 = gc.open("Desolation Player Management")
sheet_alive_characters = workbook2.worksheet("Character's Alive")

colexp = 11
colitem = 12
colgold = 10
maxsignups = 40
colpriority = 16

if testing == 1:
	questid = 816341640133869568
	botspamdm = 815606288498819094
	botspamplayer = 816351222013100072
else:
	questid = 690302160465952906
	botspamdm = 817805134733246485
	botspamplayer = 817805569758593076

'''
session['allowed'] = 
'''

emojilist = (
	"🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮", "🇯", "🇰", "🇱", "🇲", "🇳", "🇴", "🇵", "🇶", "🇷", "🇸",
	"🇹", "🇺", "🇻", "🇼", "🇽", "🇾", "🇿")


# New - The Cog class must extend the commands.Cog class
class session(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		if payload.user_id == self.bot.user.id:  # Check to make sure the bot did not send the message
			return
		if payload.channel_id != questid:  # Only runs commands in the Quest id channel
			return

		channel = self.bot.get_channel(payload.channel_id)  # Get Channel that the request camefrom. Used to check to see where the message came from
		message = await channel.fetch_message(payload.message_id)  # Get the message that was reacted to. Used for deleting messages
		user = self.bot.get_user(payload.user_id)  # Used to delete emoji
		await message.remove_reaction(payload.emoji, user)  # Delete the emoji so players can't tell who signed up.

		#  End a session. Will prompt user for information to give out xp and such.
		if payload.emoji.name == "🔚":
			developer = False  # Set Developer to False To check if the user is a developer
			dm = False  # Check to see if the user is a DM or a Trial DM
			for role in payload.member.roles:  # Go through all roles to see if they are a Developer, or DM
				if role.name == "Developer":
					developer = True
					break
				elif role.name == "DM":
					dm = True
				elif role.name == "Trial DM":
					dm = True
			if not (developer or dm):  # If the user is not a developer or DM then cancel request.
				msg = await payload.member.send(
					"You do not have permission to cancel this post. If you believe this is an error message a Developer.")
				return
			batch_active_session = sheet_activesession.get_all_records()  # Get Session information
			if len(batch_active_session) < 1:  # If no session was found allows the user to just cancel the session. This would be caused if a row was deleted on the google sheet.
				choice = await emojiconfirm(self, payload, "No Session's Found. Would you like to delete the posting?")
				if choice == -1:  # If the person did not select anything it will timeout
					await payload.member.send("Timeout. ReReact to start again.")
					return
				elif not choice:  # The user choose not to delete the request
					await payload.member.send("Message will not be deleted.")
					return
				elif choice:  # The user choose to delete the request.
					await try_delete(message)
					await payload.member.send("Message Deleted")
					return
				else:  # Unexpected error
					await payload.member.send("Error of some sort. Not handled")
					return
				return
			foundsession = False  # Search through the database to find a selected session
			row = 2  # The row on the gsheet the session was in.
			for sessions in batch_active_session:  # Search through to find if the user is the owner of said session.
				if sessions["MessageID"] == payload.message_id:  # Find the reacted to message
					if sessions["HostID"] == payload.user_id:  # Is the user the host.
						foundsession = True
						break
					elif developer:  # Is the user a developer
						foundsession = True
						break
				row += 1
			if not foundsession:  # User does not have rights to end said message.
				await payload.member.send(
					"You do not have permission to cancel this post. If you believe this is an error message a Developer. ")
				return
			chan_botspamdm = self.bot.get_channel(botspamdm)  # Get place to post dm messages
			choice = await emojimulti(self, chan_botspamdm, ("Yes", "No"),
									  f"<@!{payload.user_id}>\nDo you want to Start the process of Finishing a Session?\nYou Should have XP / Gold / Players and items rewarded ready before.",
									  payload.user_id)
			if choice == -1:  # Timedout.
				await chan_botspamdm.send("Timeout. ReReact to start again.")
				return
			elif not choice:  # User choose not to complete session at this time
				await chan_botspamdm.send("Message will not be deleted.")
				return
			elif choice:  # User will start completeing message
				pass
			else:   # Unacounted for error
				await chan_botspamdm.send("Unknown Error. Message Developer. Or Don't add your own reactions....")

			batch_session_details = sheet_joinlist.get_all_records()  # Get joinlist.

			for sessiondetails in batch_session_details:  # Find all matching sessions
				if sessiondetails["MessageID"] == payload.message_id:
					break
			cast = []  # Get the cast of everyone who signedup for the session
			if sessiondetails["Signup Count"] == 0:  # Error out if no one signed up
				await chan_botspamdm.send("There are no players signed up yet.")
				return  # TODO: Add the ability for the user to delete the message.
			elif sessiondetails["Signup Count"] == 1:  # If only one user is found just return that users information
				characterssplit = sessiondetails["All Character's"]
				discordsplit = sessiondetails["All Discord ID's"]
				cast.characterschosen = f"<@!{discordsplit}>, {characterssplit}"
			else:  # Split the users
				characterssplit = sessiondetails["All Character's"].split(",")
				discordsplit = sessiondetails["All Discord ID's"].split(",")
				x = 0
				for x in range(0, len(characterssplit)): # Go through all use users in the list and get the appropraite dicord id and character name.
					cast.append((f"<@!{discordsplit[x]}>, {characterssplit[x]}"))  # Add characters to display dicord name correctly on discord
					x += 1
				characterschosen, manual = await emojimulti(self, chan_botspamdm, cast,
															f"<@!{payload.user_id}>\nSelect the Characters who came to the session.",
															payload.user_id, multi=True) #  Go though all the people who signed up to select who came to the session.
				if manual == -1:  # When timeout error out
					await payload.member.send("Timeout. ReReact to start again.")
					return
			xpinput = await getinput(self, chan_botspamdm,
									 f"<@!{payload.user_id}>\nHow Much XP Per Character To Reward? Limits:\n{sessiondetails['Experience Cap']}", payload.user_id,
									 delete_msgs=True, time=120)  # Get how much xp the players should recieve
			if not RepresentsInt(xpinput):  # Error out if they entered a number that cant conver to an int.
				chan_botspamdm.send("SE100 - You did not enter a number. Exiting")
				return
			xpinput = int(xpinput)
			experiencesplit = sessiondetails["Experience Cap"].split(",")
			if xpinput > int(experiencesplit[3]):  # if experience is given out higher then the deadly. Lower xp to deadly.
				xpintput = int(experiencesplit[3])
			handoutarray = []  # Start out a fresh array for things gave out. Each should be serpated by a comma
			for temp in characterschosen:  # Go through all the people that were selected by the DM.
				input = await getinput(self, chan_botspamdm,
									   f"<@!{payload.user_id}>\nFor {temp} Enter Items\n# itemname\n# = amount\nitemname = name of the item. New entries seperated by a comma",
									   payload.user_id, delete_msgs=True, time=120)  # Go through cast and add items to each
				handoutarray.append(input.lower())  # convert item list to lower
			sendmsg = f"<@!{payload.user_id}>\n**XP:** {xpinput}\n-----------------\n"  # get the player to confirm all the items given out.
			for temp in range(0, len(characterschosen)):  # go through list to send to the DM to approve. TODO: convert to long msg at some point
				sendmsg = sendmsg + f"**Player:**\n{characterschosen[temp]}\n{handoutarray[temp]}\n-----------------\n"
			choice = await emojimulti(self, chan_botspamdm, ("Yes", "No"), sendmsg, payload.user_id, time=300)  # Does the DM Approve reward
			if choice == -1:  # Took to long so timeout out
				await chan_botspamdm.send("Timeout. ReReact to start again.")
				return
			elif not choice:  # Rejected so ending. Will need to be restarted from beginning.
				await chan_botspamdm.send("Rejected Results. Restart with Rereacting...Sorry good luck...")
			batch_get_characters = sheet_characters.get_all_records()  # Get all players
			x = 0  # Variable for looking at handoutarray
			cells = []  # an array for the cells to be updated in the googlespreadsheet
			characternamearray = ""
			itemarray = ""
			for a in characterschosen:  # go through all members of the cast to add items to. TODO: add the dm as well in here in the beginning
				splitcast = a.split(",")  # split the id from the character name
				aid = splitcast[0].replace("<", "")  # remove all the discord friendly parts of the ID
				aid = aid.replace("@", "")
				aid = aid.replace("!", "")
				aid = aid.replace(">", "")
				aid = int(aid)  # convert ID from string to INT
				aname = splitcast[1].strip(" ")  # remove leading and post blank spaces
				frow = 2  # variable for what row the character was found in.
				characternamearray = characternamearray + f" {aname} |"
				itemarray = itemarray + f" {handoutarray[x]} |"
				for b in batch_get_characters:  # loop through the spreadsheet to find the matching cast member's row
					if b["DiscordID"] == aid:  # matching spreadsheet row to dicord id
						if b["Name"] == aname:  # matching spreadsheet row to cast name
							if RepresentsInt(b['Gold']):  # get spreadsheet gold and check if it is an int.
								gold = int(b['Gold'])  # if it is convert to int.
							else:
								gold = 0  # If not a int set gold to starting value of 0. Needed for if the gold space is blank
							if RepresentsInt(b["Experience"]):  # Get experience the player has and convert it to int.
								expereience = int(b["Experience"]) + xpinput  # add existing exp to session exp
							else:
								expereience = int(xpinput)  # if experience is blank set to session exp
							splithandout = handoutarray[x].split(",")  # Get number of items handed out to player
							playersitems = b["Items"]  # get players current items
							playersitemssplit = playersitems.split(",")  # split players current items by comma
							if splithandout[0] == "none":  # Check to see if they didnt recieve anything
								pass
							elif splithandout[0] == "nothing":
								pass
							elif splithandout[0] == "na":
								pass
							elif splithandout[0] == "n/a":
								pass
							else:
								for items in splithandout:  # loop through all items the player is being given.
									item = items.strip()  # remove blank spaces before and after.
									itemsplit = item.split(" ", 1)  # split at first space between amount and item name.
									if len(itemsplit) < 2:  # if there was no split dont add to player
										await chan_botspamdm.send(
											f"Error 103: <@!{payload.user_id}> the item {item} was not added to {b['Name']}.Was likely missing an amount or name")
									else:  # check to see if the amount is a number. If not dont add the item.
										if not RepresentsInt(itemsplit[0]):
											await chan_botspamdm.send(
												f"Error 104: <@!{payload.user_id}> the item {item} was not added to {b['Name']}. Item Did not have a number.")
										else:  # Add the item to the plaer
											itemamount = int(itemsplit[0])  # Convert amount to an int
											if itemsplit[1] == "gold":  # If the item is currency add it to gold based on value
												gold = gold + itemamount
											elif itemsplit[1] == "silver":
												gold = gold + (itemamount / 10)
											elif itemsplit[1] == "copper":
												gold = gold + (itemamount / 100)
											elif itemsplit[1] == "platinum":
												gold = gold + (itemamount * 10)
											else:  # If not gold add the item to the players items
												match = False  # Variable to see if the item exist in the inventory already
												d = 0  # variable to search through array used if there is a match to know where to add
												for pitems in playersitemssplit:  # look through existing items
													if pitems == "":  # If the item space is blank just end. They have no items
														break
													else:  # If they do have items strip out the space and split between amount and name
														pitems = pitems.strip()
														pitems = pitems.split(" ", 1)
														if len(pitems) < 2:  # is this split correctly?
															pass
														else:  # if it is
															if pitems[1] == itemsplit[1]:  # Does the name of the new item match the name of the current item?
																if not RepresentsInt(pitems[0]):  # If so is the amount an actual item
																	f"Error 105: <@!{payload.user_id}> the item {item} was not added to {b['Name']}."
																	break # break for loop as this item was not entered correctly
																playersitemssplit[
																	d] = f"{int(pitems[0]) + itemamount} {pitems[1]}"  # add amount to existing amount
																match = True  # dont add a new item
																break  # item found
														d += 1  # search next item
												if not match:  # item not found in current items time to add a new one
													playersitemssplit.append(f"{itemamount} {itemsplit[1]}")
							newitemstring = ""  # start a new string for item names
							c = 1  # row 1 of the spreadsheet
							for items in playersitemssplit:  # Create new list of items
								if not items == "":
									if len(playersitemssplit) > c:
										newitemstring = newitemstring + items + ","
									else:
										newitemstring = newitemstring + items
								c += 1
							timepriority = datetime.datetime.now()  # Get current time and date to be listed as when they requested to join the session. This is used in the second frame as it is first come first serve.
							priority = f"{timepriority.month}/{timepriority.day}/{timepriority.year} {timepriority.hour}:{timepriority.minute}:{timepriority.second}.{timepriority.microsecond}"
							celldata = get_cell_for_update((gold, expereience, newitemstring, priority), (frow, frow, frow, frow),
														   (colgold, colexp, colitem, colpriority))  # send items to gsheet to update session details
							for temp in celldata:  # add to cell array
								cells.append(temp)
							break
					else:
						frow += 1  # update to search through next row
				x += 1  # update to search for next cast
			logger("Session", [str(sessiondetails['HostID']), sessiondetails['Experience Cap'], xpinput, characternamearray, itemarray])
			sheet_characters.update_cells(cells, value_input_option="USER_ENTERED")  # move data to google sheet
			sheet_activesession.delete_row(row)  # delete session from google sheet
			await try_delete(message)  # delete message from discord
			await chan_botspamdm.send("Post Completed")  # let dm know everything completed
			return  # end completing session

		# Get Session Information.
		elif payload.emoji.name == "❔":  # Get Information about Active Session
			developer = False  # variable to check to see if the user is a developer
			dm = False  # check to see if the user has a dm role
			for role in payload.member.roles:  # check the users roles for dm or developer
				if role.name == "Developer":
					developer = True
					break
				elif role.name == "DM":
					dm = True
				elif role.name == "Trial DM":
					dm = True
			if not (developer or dm):  # cancel out if the user does not have the permisions needed
				msg = await payload.member.send(
					"You do not have permission to get results of this post. If you believe this is an error message a Developer.")
				return
			batch_get_joinlist = sheet_joinlist.get_all_records()  # get all the sessions
			if len(batch_get_joinlist) < 1:  # end if there was no sessions detected. Shouldnt ever happen
				await payload.member.send("An Error has been detected. No Session's Found")
				return
			activesession = False  # variable to check to see if the message has a session t
			for sessionmatch in batch_get_joinlist:  # look through list to if the message has a attached session
				if sessionmatch["MessageID"] == payload.message_id:  # does the message id match this session
					activesession = True  # there is a session avaliable
					break
			if not activesession:  # no session match found
				await payload.member.send("An Error has been detected. No Session's Found")
				return
			if sessionmatch["Signup Count"] == 0:  # how many people are signed up. No point of returning info if no one.
				await payload.member.send("There are no players signed up yet.")
				return
			elif sessionmatch["Signup Count"] == 1:  # if only one person signed up just return there information
				characterssplit = sessionmatch["Character's Chosen"]
				levelssplit = sessionmatch["Level's Chosen"]
				discordsplit = sessionmatch["Discord ID's Chosen"]
				cast = f"__Cast__\n**Player:** <@!{discordsplit}> | **Character:** {characterssplit} | **Level:** {levelssplit}\n"  # TODO: Add Class as well
			else:  # if multi people signedup return entire cast.
				characterssplit = sessionmatch["All Character's"].split(",")  # split up characters
				levelssplit = sessionmatch["All Level's"].split(",")  # split up levels
				discordsplit = sessionmatch["All Discord ID's"].split(",")  # split up discord ids
				cast = "__Cast__\n"  # title for discord
				x = 0  # variable to search through
				for x in range(0, sessionmatch["Signup Count"]-1):  # loop through allowed signups and add them
					cast = cast + f"**Player:** <@!{discordsplit[x]}> | **Character:** {characterssplit[x]} | **Level:** {levelssplit[x]}\n"
					if x >= sessionmatch["Player Count"]-1:  # if you hit the player cap break out
						break
				if sessionmatch["Player Count"] < sessionmatch["Signup Count"]:  # If the session has extra players add two for cast.
					cast = cast + f"__Extra Player's  if Needed__\n"
					if x < sessionmatch["Signup Count"]-1:
						cast = cast + f"**Player:** <@!{discordsplit[x]}> | **Character:** {characterssplit[x]} | **Level:** {levelssplit[x]}\n"
						x += 1
					if x < sessionmatch["Signup Count"] - 1:
						cast = cast + f"**Player:** <@!{discordsplit[x]}> | **Character:** {characterssplit[x]} | **Level:** {levelssplit[x]}\n"
						x += 1
			experiencesplit = sessionmatch["Experience Cap"].split(",")  # split up exp cap
			goldsplit = sessionmatch["Gold Cap"].split(",")  # split up gold cap
			chan_botspamdm = self.bot.get_channel(botspamdm) # get dm channel
			x = 0  # start a new search variable
			xpgold = "__Xp/Gold Cap Per Session Not Per Person__\n"  # start a new area of the post
			for x in range(0, len(experiencesplit)):  # loop through all the variables
				if x == 0:
					xpgold = xpgold + "**Easy:** "
				elif x == 1:
					xpgold = xpgold + "**Normal:** "
				elif x == 2:
					xpgold = xpgold + "**Hard:** "
				else:
					xpgold = xpgold + "**Deadly:** "
				xpgold = xpgold + f"XP: {experiencesplit[x]} |  Gold: {goldsplit[x]}\n"  # get xp gold splits
			datentime = "__Date/Time__\n" + sessionmatch["Date/Time"] + "\n"  # get date of the session
			hostid = sessionmatch["HostID"]  # get who is hosting the session
			host = f"__Host__\n <@!{hostid}> \n"  # conver to discord recognized mention
			signupsallowed = f"__Allowed Slots__\n{sessionmatch['Player Count']} \n"  # number of people allowed to signup
			sessionassignment = f"__Session__\n{sessionmatch['Assignment']} \n"  #  what letter it is to sign up
			grace = f"__Grace Periods Ends__\n{sessionmatch['Grace']} \n"  # when the grace period ends.
			sendmsg = sessionassignment + datentime + grace + host + signupsallowed + xpgold + cast  # the msg to post in chat
			await sendlong(chan_botspamdm, sendmsg)  # check to see if the msg is over 2000 characters
			return  # end

		# Attempt signup for a specific session
		else:  # Used for signing up to a session
			chan_botspamplayer = self.bot.get_channel(botspamplayer)  # Get the channel that the messages will be sent to for the player.
			batch_get_signups = sheet_signups.get_all_records()  # Get all people signedup to the session TODO: in the future change this to just use the joinlist to search
			signedup = search_dictionary(batch_get_signups, ['DiscordID', 'MessageID'],
										 [payload.user_id, payload.message_id], ['==', '=='])  #  Look to see if the player has already signedup
			if not signedup is None:  # If the player has signedup exit. Telling them they have and when.
				await payload.member.send(
					f"You are already signed up for session {signedup[0]['Assignment']} with character {signedup[0]['Character']} at {signedup[0]['Timestamp']}.")
				return
			batch_get_joinlist = sheet_joinlist.get_all_records()  # Get session information
			session = search_dictionary(batch_get_joinlist, ['MessageID'], [payload.message_id], ['=='])  # Get specific session information
			if session is None:
				await payload.member.send("Error 1: Alert the Developer")  # No Session was found. Message needs to be deleted
				return
			session = session[0]  # Convert found session to non list database.
			if session['Signup Count'] >= maxsignups:  # If the signups have reached max signups cancel. This can be set to a maximum of 49. This prevents an overflow on the google sheet. which is set to 50 rows
				await payload.member.send("Session has reached max signups.")
				return
			batch_get_characters = sheet_alive_characters.get_all_records()  # get all alive character records Then search to see if they have matching characters using criteria setup in the session.
			if session['Allowed'] == 0:  # Only Characters in Range
				characters = search_dictionary(batch_get_characters, ['DiscordID', 'DiscordID', 'Level', 'Level'],
											   [payload.user_id, session['HostID'], session['Min'], session['Max']],
											   ['==', '!=', '>=', '<='])
			elif session['Allowed'] == 10 or session['Allowed'] == 100:  # Lower Characters Allowed
				characters = search_dictionary(batch_get_characters, ['DiscordID', 'DiscordID', 'Level'],
											   [payload.user_id, session['HostID'],session['Max']],
											   ['==', '!=', '<='])

			elif session['Allowed'] == 20 or session['Allowed'] == 200:  # Higher Characters Allowed
				characters = search_dictionary(batch_get_characters, ['DiscordID', 'DiscordID', 'Level'],
											   [payload.user_id, session['HostID'],session['Min']],
											   ['==', '!=', '>='])

			else:  # All Characters Allowed
				characters = search_dictionary(batch_get_characters, ['DiscordID', 'DiscordID'],
											   [payload.user_id, session['HostID']],
											   ['==', '!='])
			if characters is None:  # The character has no eligable characters.
				await payload.member.send("You Have no Character's that are eligible for the current session.\nThis "
										  "could be due to not being in the missions allowed target range, because you "
										  "are hosting the session\n or because you have no alive characters "
										  "setup.\nIf you believe this is an error contact a Developer.")
				return
			elif len(characters) == 1:  # If there is only one character convert to not list.
				character = characters[0]
			else:
				charactername = await emojimulti(self, chan_botspamplayer, get_dictionary_key(characters, 'Name'),
												 "Which Character?", who=payload.user_id)  #  If they have multiple eligable characters ask which one they want to use.
				for a in characters:  # Find what character was selected.
					if a['Name'] == charactername:
						character = a
			if session['Allowed'] == 10:  # Determine if the character is in the range critereia set in the session. 1 is for priority signups, 0 is for non priority. They should not be able to get here with a character that is not in the allowed level range
				if character["Level"] >= session['Min']:
					inrange = 1
				else:
					inrange = 0
			elif session['Allowed'] == 20:
				if character["Level"] <= session['Max']:
					inrange = 1
				else:
					inrange = 0
			elif session['Allowed'] == 9:
				if session['Min'] <= character["Level"] >= session['Max']:
					inrange = 1
				else:
					inrange = 0
			else:
				inrange = 1
			timeposted = datetime.datetime.now()  # Get current time and date to be listed as when they requested to join the session. This is used in the second frame as it is first come first serve.
			sheet_signups.append_row([
				f"{timeposted.month}/{timeposted.day}/{timeposted.year} {timeposted.hour}:{timeposted.minute}:{timeposted.second}.{timeposted.microsecond}",
				payload.emoji.name, character['Name'], str(payload.message_id),
				str(payload.user_id), inrange], value_input_option='USER_ENTERED',
				insert_data_option="INSERT_ROWS", table_range="A1")  # Add request to signup sheet. Google sheet handles the rest.
			await payload.member.send(
				f"You have signed up for session {payload.emoji.name} with character {character['Name']}.")  # Send the user a message telling them they signed up.
			return
		return

	# This command is for creating new sessions
	@commands.command(
		name='newsession',
		description="posts a new session for players to react to, to sign up.",
		hidden=True,
		aliases=['ns']
	)
	async def NSCommand(self, ctx, *, information):
		if not await checkperm(ctx, "DM", messageuser=False):  # check to see if the person is a dm or trial dm
			if not await checkperm(ctx, "Trial DM",
								   message="You must have the Trial DM or DM Role to use this command"):
				return
		if not ctx.channel.category.name == "Quest":  # check to see if the command was in the correct category
			await ctx.author.send("Needs to be posted in the #Quest Category in the new channel")
			return
		if not ctx.channel.name == "new":  # check to see if the command was in the correct channel
			await ctx.author.send("Needs to be posted in the new category")
			return
		"""
		The area below pulls information for the message needed for the session.
		"""
		datestart = information.find("Date=")
		if datestart == -1:
			await ctx.author.send("Missing Date=")
			return
		dateend = information.find("\n", datestart)
		if dateend == -1:
			await ctx.author.send("Missing Newline after Date")
			return
		date = information[datestart + 5:dateend]
		whostart = information.find("Who=")
		if whostart == -1:
			await ctx.author.send("Missing Who=")
			return
		whoend = information.find("\n", whostart)
		if whoend == -1:
			await ctx.author.send("Missing Newline after Who")
			return
		who = information[whostart + 4:whoend]
		programstart = information.find("Program=")
		if programstart == -1:
			await ctx.author.send("Missing Program=")
			return
		programend = information.find("\n", programstart)
		if programend == -1:
			await ctx.author.send("Missing Newline after programstart")
			return
		program = information[programstart + 8:programend]
		timestart = information.find("Time=")
		if timestart == -1:
			await ctx.author.send("Missing Time=")
			return
		timeend = information.find("\n", timestart)
		if timeend == -1:
			await ctx.author.send("Missing New Line after Time")
			return
		time = information[timestart + 5:timeend]
		allowedstart = information.find("Allowed=")
		if allowedstart == -1:
			await ctx.author.send("Missing Allowed=")
			return
		allowedend = information.find("\n", allowedstart)
		if allowedend == -1:
			await ctx.author.send("Missing Newline after Allowed")
			return
		allowed = information[allowedstart + 8: allowedend]
		descriptionstart = information.find("Desc=")
		if descriptionstart == -1:
			await ctx.author.send("Missing Desc=")
			return
		descriptionend = len(information)
		description = information[descriptionstart + 5:descriptionend]
		durationstart = information.find("Length=")
		if durationstart == -1:
			await ctx.author.send("Missing Length=")
			return
		durationend = information.find("\n", durationstart)
		if durationend == -1:
			await ctx.author.send("Missing New line after Length")
			return
		duration = information[durationstart + 7:durationend]
		host = ctx.author.mention
		playerstart = information.find("Player=")
		if playerstart == -1:
			player = "5"
		else:
			playerend = information.find("\n", playerstart)
			player = information[playerstart + 7:playerend]

		low = 0  # lowest level taged
		high = 0  # highest level tagged
		# Area below checks to get the lowest and highest levels of the people in the role tag.
		for p in ctx.message.role_mentions:
			p.name = p.name.replace(" ", "")
			rolesplit = p.name.split("-")
			if len(rolesplit) < 2:
				pass
			else:
				if not RepresentsInt(rolesplit[0]):
					pass
				else:
					for temp in rolesplit:
						if not RepresentsInt(temp):
							pass
						else:
							value = int(temp)
							if low == 0:
								low = value
							elif low > value:
								low = value
							if high == 0:
								high = value
							elif high < value:
								high = value

		if allowed == "0":
			allowedtxt = "In - Range Only"
		elif allowed == "10":
			allowedtxt = "Lower allowed but In-Ranged preferred"
		elif allowed == "100":
			allowed = "Lower and In - Range"
		elif allowed == "20":
			allowedtxt = "Higher allowed but In-Ranged preferred."
		elif allowed == "200":
			allowedtxt = "Higher and In - Range"
		elif allowed == "9":
			allowedtxt = "all allowed - in range preferred"
		else:
			allowed = 900
			allowedxt = "all allowed"
		desc = f"\n**Date:** {date}\n**Time:** {time} EST\n**Length:** {duration}\n**Host:** {host}\n**Who:** {who}\n**Program:** {program}\n**Description:** {description}"

		if len(desc) > 2000:
			await ctx.channel.send(
				f"{host}\nThe message has a maximum of 2000 characters. You are currently at {len(desc)}")
			return

		sendmsg = await ctx.channel.send(desc)
		await sendmsg.add_reaction(get_emoji(ctx, "Approved"))
		await sendmsg.add_reaction(get_emoji(ctx, "Rejected"))

		def check(reaction, user):
			return user == ctx.message.author

		try:
			reaction, user = await self.bot.wait_for('reaction_add', timeout=120.0, check=check)
		except asyncio.TimeoutError:
			await try_delete(sendmsg)
			return
		else:
			if reaction.emoji.name == 'Approved':
				batch_get_activesessions = sheet_activesession.get_all_records()
				if len(batch_get_activesessions) is 0:
					assignedemogi = emojilist[0]
				else:
					for emoji in emojilist:
						assignment = 1
						for sessions in batch_get_activesessions:
							if sessions["Assignment"] == emoji:
								assignment = 0
								break
						if assignment == 1:
							assignedemogi = emoji
							break
							await ctx.message.send("To Many Quests Posted Currently")
				await try_delete(ctx.message)
				await try_delete(sendmsg)
				channel = self.bot.get_channel(questid)
				questactive = await channel.send(desc)
				timeposted = utc_to_local(ctx.message.created_at)
				sheet_activesession.append_row(
					[f"{date} {time}", time, duration, ctx.author.nick, who, assignedemogi, description,
					 str(ctx.author.id), str(questactive.id),
					 f"{timeposted.month}/{timeposted.day}/{timeposted.year} {timeposted.hour}:{timeposted.minute}",
					 player, low, high, allowed], value_input_option='USER_ENTERED', insert_data_option="INSERT_ROWS",
					table_range="A1")
				await questactive.add_reaction(assignedemogi)
				return
			if reaction.emoji.name == "Rejected":
				await try_delete(sendmsg)
				return


def setup(bot):
	bot.add_cog(session(bot))
# Adds the Basic commands to the bot
# Note: The "setup" function has to be there in every cog file
