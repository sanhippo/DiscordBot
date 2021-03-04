import gspread
from utils.functions import checkperm, get_emoji, try_delete, utc_to_local, emojiconfirm, sendlong, emojimulti, \
	getcharacters, getinput, RepresentsInt
import asyncio
from discord.ext import commands
from credentials import testing
import datetime
from cogs.playercharacter import sheet_characters

gc = gspread.service_account()
workbook = gc.open("Desolation - Session Join Request")
sheet_activesession = workbook.worksheet("ActiveSessions")
sheet_signups = workbook.worksheet("signups")
sheet_joinlist = workbook.worksheet("Test")


if testing == 1:
	questid = 816341640133869568
	botspamdm = 815606288498819094
	botspamplayer = 816351222013100072
else:
	questid = 690302160465952906

emojilist = (
	"🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮", "🇯", "🇰", "🇱", "🇲", "🇳", "🇴", "🇵", "🇶", "🇷", "🇸",
	"🇹", "🇺", "🇻", "🇼", "🇽", "🇾", "🇿")


# New - The Cog class must extend the commands.Cog class
class session(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		if payload.user_id == self.bot.user.id:
			return
		if payload.channel_id != questid:
			return

		channel = self.bot.get_channel(payload.channel_id)
		message = await channel.fetch_message(payload.message_id)
		user = self.bot.get_user(payload.user_id)
		await message.remove_reaction(payload.emoji, user)

		if payload.emoji.name == "🔚":
			developer = False
			dm = False
			for role in payload.member.roles:
				if role.name == "Developer":
					developer = True
					break
				elif role.name == "DM":
					dm = True
				elif role.name == "Trial DM":
					dm = True
			if not (developer or dm):
				msg = await payload.member.send(
					"You do not have permission to cancel this post. If you believe this is an error message a Developer.")
				return
			batch_active_session = sheet_activesession.get_all_records()
			if len(batch_active_session) < 1:
				choice = await emojiconfirm(self, payload, "No Session's Found. Would you like to delete the posting?")
				if choice == -1:
					await payload.member.send("Timeout. ReReact to start again.")
					return
				elif not choice:
					await payload.member.send("Message will not be deleted.")
					return
				elif choice:
					await payload.member.send("Message Deleted")
				else:
					await payload.member.send("Error of some sort. Not handled")
					return
				return
			foundsession = False
			row = 2
			for sessions in batch_active_session:
				if sessions["MessageID"] == payload.message_id:
					if sessions["HostID"] == payload.user_id:
						foundsession = True
						break
					elif developer:
						foundsession = True
						break
				row += 1
			if not foundsession:
				await payload.member.send(
					"You do not have permission to cancel this post. If you believe this is an error message a Developer. ")
				return
			chan_botspamdm = self.bot.get_channel(botspamdm)
			choice = await emojimulti(self, chan_botspamdm, ("Yes", "No"), f"<@!{payload.user_id}>\nDo you want to Start the process of Finishing a Session?\nYou Should have XP / Gold / Players and items rewarded ready before.", payload.user_id)
			if choice == -1:
				await chan_botspamdm.send("Timeout. ReReact to start again.")
				return
			elif not choice:
				await chan_botspamdm.send("Message will not be deleted.")
				return
			elif choice:
				pass
			else:
				await chan_botspamdm.send("Unknown Error. Message Developer. Or Don't add your own reactions....")

			batch_session_details =sheet_joinlist.get_all_records()

			for sessiondetails in batch_session_details:
				if sessiondetails["MessageID"] == payload.message_id:
					break
			cast = []
			if sessiondetails["Signup Count"] == 0:
				await chan_botspamdm.send("There are no players signed up yet.")
			elif sessiondetails["Signup Count"] == 1:
				characterssplit = sessiondetails["All Character's"]
				discordsplit = sessiondetails["All Discord ID's"]
				cast.append(f"<@!{discordsplit}>, {characterssplit}")
			else:
				characterssplit = sessiondetails["All Character's"].split(",")
				discordsplit = sessiondetails["All Discord ID's"].split(",")
				x = 0
				for x in range(0, len(characterssplit)):
					cast.append((f"<@!{discordsplit[x]}>, {characterssplit[x]}"))
					x += 1
				characterschosen, manual = await emojimulti(self, chan_botspamdm, cast, f"<@!{payload.user_id}>\nSelect the Characters who came to the session.", payload.user_id, multi=True)
				if manual == -1:
					await payload.member.send("Timeout. ReReact to start again.")
					return

			xpinput = await getinput(self, chan_botspamdm, f"<@!{payload.user_id}>\nHow Much XP Per Character To Reward?", payload.user_id, delete_msgs=True, time=120)
			if not RepresentsInt(xpinput):
				chan_botspamdm.send("SE100 - You did not enter a number. Exiting")
				return
			handoutarray = []
			for temp in cast:
				input = await getinput(self, chan_botspamdm, f"<@!{payload.user_id}>\nFor {temp} Enter Items\n# itemname\n# = amount\nitemname = name of the item. New entries on seperate lines using shift + enter.", payload.user_id, delete_msgs=True, time=120)
				handoutarray.append(input.lower())
			sendmsg = f"<@!{payload.user_id}>\n**XP:** {xpinput}\n-----------------\n"
			for temp in range(0, len(cast)):
				sendmsg = sendmsg + f"**Player:**\n{cast[temp]}\n{handoutarray[temp]}\n-----------------\n"
			choice = await emojimulti(self, chan_botspamdm, ("Yes", "No"), sendmsg, payload.user_id, time=300)
			if choice == -1:
				await chan_botspamdm.send("Timeout. ReReact to start again.")
				return
			elif not choice:
				await chan_botspamdm.send("Rejected Results. Restart with Rereacting...Sorry good luck...")
			batch_get_characters = sheet_characters.get_all_records()

			x = 0
			for a in cast:
				splitcast = a.split(",")
				aid = splitcast[0].replace("<", "")
				aid = aid.replace("@", "")
				aid = aid.replace("!", "")
				aid = aid.replace(">", "")
				aid = int(aid)
				aname = splitcast[1].replace(" ", "")
				for b in batch_get_characters:
					if b["DiscordID"] == aid:
						if b["Name"] == aname:
							expereience = int(b["Experience"]) + int(xpinput)
							splithandout = handoutarray[x].split("\n")
							print("Hey")
				x += 1









			return
			sheet_activesession.delete_row(row)
			await try_delete(message)
			await payload.member.send("Message Deleted")
			return

		if payload.emoji.name == "❔":  # Get Information about Active Session
			developer = False
			dm = False
			for role in payload.member.roles:
				if role.name == "Developer":
					developer = True
					break
				elif role.name == "DM":
					dm = True
				elif role.name == "Trial DM":
					dm = True
			if not (developer or dm):
				msg = await payload.member.send(
					"You do not have permission to get results of this post. If you believe this is an error message a Developer.")
				return
			batch_get_joinlist = sheet_joinlist.get_all_records()
			if len(batch_get_joinlist) < 1:
				await payload.member.send("An Error has been detected. No Session's Found")
				return
			activesession = False
			for sessionmatch in batch_get_joinlist:
				if sessionmatch["MessageID"] == payload.message_id:
					activesession = True
					break
			if not activesession:
				await payload.member.send("An Error has been detected. No Session's Found")
				return
			if sessionmatch["Signup Count"] == 0:
				await payload.member.send("There are no players signed up yet.")
			elif sessionmatch["Signup Count"] == 1:
				characterssplit = sessionmatch["Character's Chosen"]
				levelssplit = sessionmatch["Level's Chosen"]
				discordsplit = sessionmatch["Discord ID's Chosen"]
				cast = f"__Cast__\n**Player:** <@!{discordsplit}> | **Character:** {characterssplit} | **Level:** {levelssplit}\n"
			else:
				characterssplit = sessionmatch["Character's Chosen"].split(",")
				levelssplit = sessionmatch["Level's Chosen"].split(",")
				discordsplit = sessionmatch["Discord ID's Chosen"].split(",")
				cast = "__Cast__\n"
				x = 0
				for x in range(0, len(characterssplit)):
					cast = cast + f"**Player:** <@!{discordsplit[x]}> | **Character:** {characterssplit[x]} | **Level:** {levelssplit[x]}\n"
					x += 1

			experiencesplit = sessionmatch["Experience Cap"].split(",")
			goldsplit = sessionmatch["Gold Cap"].split(",")
			chan_botspamdm = self.bot.get_channel(botspamdm)
			x = 0
			xpgold = "__Xp/Gold Cap Per Session Not Per Person__\n"
			for x in range(0, len(experiencesplit)):
				if x == 0:
					xpgold = xpgold + "**Easy:** "
				elif x == 1:
					xpgold = xpgold + "**Normal:** "
				elif x == 2:
					xpgold = xpgold + "**Hard:** "
				else:
					xpgold = xpgold + "**Deadly:** "
				xpgold = xpgold + f"XP: {experiencesplit[x]} |  Gold: {goldsplit[x]}\n"
			datentime = "__Date/Time__\n" + sessionmatch["Date/Time"] + "\n"
			hostid = sessionmatch["HostID"]
			host = f"__Host__\n <@!{hostid}> \n"
			signupsallowed = f"__Allowed Slots__\n{sessionmatch['Player Count']} \n"
			sessionassignment = f"__Session__\n{sessionmatch['Assignment']} \n"
			grace = f"__Grace Periods Ends__\n{sessionmatch['Grace']} \n"
			sendmsg = sessionassignment + datentime + grace + host + signupsallowed + xpgold + cast
			await sendlong(chan_botspamdm, sendmsg)
			return

		'''
		This Section is for actual signups. 
		'''

		chan_botspamplayer = self.bot.get_channel(botspamplayer)
		characters = getcharacters(int(payload.user_id), what="Name")
		if characters is None:
			await payload.member.send("You currently have no character's setup. Message a Developer for Help.")
			return
		character = await emojimulti(self, chan_botspamplayer, characters, "Which Character?", who=payload.user_id)
		batch_get_signups = sheet_signups.get_all_records()
		if len(batch_get_signups) > 0:
			for signups in batch_get_signups:
				if signups["DiscordID"] == payload.user_id:
					if signups["MessageID"] == payload.message_id:
						await payload.member.send(
							f"You are already signed up for session {signups['Assignment']} with character {signups['Character']} at {signups['Timestamp']}.")
						return
		timeposted = datetime.datetime.now()
		sheet_signups.append_row([
			f"{timeposted.month}/{timeposted.day}/{timeposted.year} {timeposted.hour}:{timeposted.minute}:{timeposted.second}.{timeposted.microsecond}",
			payload.emoji.name, character, str(payload.message_id),
			str(payload.user_id), 1], value_input_option='USER_ENTERED',
			insert_data_option="INSERT_ROWS", table_range="A1")
		await payload.member.send(
			f"You have signed up for session {payload.emoji.name} with character {character}.")
		return

	# Define a new command
	@commands.command(
		name='newsession',
		description="posts a new session for players to react to, to sign up.",
		hidden=True,
		aliases=['ns']
	)
	async def NSCommand(self, ctx, *, information):
		if not await checkperm(ctx, "DM", messageuser=False):
			if not await checkperm(ctx, "Trial DM",
									message="You must have the Trial DM or DM Role to use this command"):
				return
		if not ctx.channel.category.name == "Quest":
			await ctx.author.send("Needs to be posted in the #Quest Category in the new channel")
			return
		if not ctx.channel.name == "new":
			await ctx.author.send("Needs to be posted in the new category")
			return
		datestart = information.find("Date=")
		dateend = information.find("\n", datestart)
		date = information[datestart + 5:dateend]
		whostart = information.find("Who=")
		whoend = information.find("\n", whostart)
		who = information[whostart + 4:whoend]
		programstart = information.find("Program=")
		programend = information.find("\n", programstart)
		program = information[programstart + 8:programend]
		timestart = information.find("Time=")
		timeend = information.find("\n", timestart)
		time = information[timestart + 5:timeend]
		descriptionstart = information.find("Desc=")
		descriptionend = len(information)
		description = information[descriptionstart + 5:descriptionend]
		durationstart = information.find("Length=")
		durationend = information.find("\n", durationstart)
		duration = information[durationstart + 7:durationend]
		host = ctx.author.mention
		playerstart = information.find("Player=")
		if playerstart == -1:
			player = "5"
		else:
			playerend = information.find("\n", playerstart)
			player = information[playerstart + 7:playerend]

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
					 player], value_input_option='USER_ENTERED', insert_data_option="INSERT_ROWS", table_range="A1")
				await questactive.add_reaction(assignedemogi)
				return
			if reaction.emoji.name == "Rejected":
				await try_delete(sendmsg)
				return


def setup(bot):
	bot.add_cog(session(bot))
# Adds the Basic commands to the bot
# Note: The "setup" function has to be there in every cog file
