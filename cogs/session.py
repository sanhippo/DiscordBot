from discord.ext import commands
import datetime
import d20
import gspread
from utils.functions import checkperm, get_emoji, try_delete, utc_to_local, get_positivity, emojiconfirm
from gspread.models import Cell
import asyncio
from discord.errors import Forbidden, HTTPException, InvalidArgument, NotFound
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError
from credentials import testing


gc = gspread.service_account()
workbook = gc.open("Desolation - Session Join Request")
sheet_activesession = workbook.worksheet("ActiveSessions")
sheet_signups = workbook.worksheet("signups")
sheet_joinlist = workbook.worksheet("Test")



if testing == 1:
	questid = 814117576804007976
else:
	questid = 690302160465952906

emojilist = ("🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮", "🇯", "🇰", "🇱", "🇲", "🇳", "🇴", "🇵", "🇶", "🇷", "🇸", "🇹", "🇺", "🇻", "🇼", "🇽", "🇾", "🇿")


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
				msg = await payload.member.send("You do not have permission to cancel this post. If you believe this is an error message a Developer.")
				return
			batch_get_activesessions = sheet_activesession.get_all_records()
			channel = self.bot.get_channel(payload.channel_id)
			message = await channel.fetch_message(payload.message_id)
			if len(batch_get_activesessions) < 1:
				choice = await emojiconfirm(self, payload, "No Session's Found. Would you like to delete the posting?")
				if choice == -1:
					await payload.member.send("Timeout. ReReact to start again.")
					user = self.bot.get_user(payload.user_id)
					await message.remove_reaction(payload.emoji, user)
					return
				elif not choice:
					await payload.member.send("Message will not be deleted.")
					user = self.bot.get_user(payload.user_id)
					await message.remove_reaction(payload.emoji, user)
					return
				elif choice:
					user = self.bot.get_user(payload.user_id)
					await try_delete(message)
					await payload.member.send("Message Deleted")
				else:
					await payload.member.send("Error of some sort. Not handled")
					user = self.bot.get_user(payload.user_id)
					await message.remove_reaction(payload.emoji, user)
					return
				return
			foundsession = False
			for sessions in batch_get_activesessions:
				if sessions["MessageID"] == payload.message_id:
					if sessions["HostID"] == payload.user_id:
						foundsession = True
						break
					elif developer:
						foundsession = True
						break
			if not foundsession:
				await payload.member.send("You do not have permission to cancel this post. If you believe this is an error message a Developer. ")
				return


		if payload.emoji.name == "❔":  # Get Information about Active Session
			channel = self.bot.get_channel(payload.channel_id)
			message = await channel.fetch_message(payload.message_id)
			user = self.bot.get_user(payload.user_id)
			await message.remove_reaction(payload.emoji, user)
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

			else:

			experiencesplit = sessionmatch["Experience Cap"].split(",")
			goldsplit = sessionmatch["Gold Cap"].split(",")










		#  Add Code here to Delete

		batch_get_signups = sheet_signups.get_all_records()
		if len(batch_get_signups) > 0:
			for signups in batch_get_signups:
				if signups["DiscordID"] == payload.user_id:
					if signups["MessageID"] == payload.message_id:
						await payload.member.send(f"You are already signed up for session {payload.emoji.name}.")
						return
		timeposted = datetime.datetime.now()
		sheet_signups.append_row([f"{timeposted.month}/{timeposted.day}/{timeposted.year} {timeposted.hour}:{timeposted.minute}:{timeposted.second}.{timeposted.microsecond}", payload.emoji.name, payload.member.nick, str(payload.message_id), str(payload.user_id)], value_input_option='USER_ENTERED', insert_data_option="INSERT_ROWS", table_range="A1")
		await payload.member.send(f"You have signed up for session {payload.emoji.name}")
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
			if not await checkperm(ctx, "Trial DM", message="You must have the Trial DM or DM Role to use this command"):
				return
		if not ctx.channel.category.name == "Quest":
			await ctx.author.send("Needs to be posted in the #Quest Category in the new channel")
			return
		if not ctx.channel.name == "new":
			await ctx.author.send("Needs to be posted in the new category")
			return
		datestart = information.find("Date=")
		dateend = information.find("\n", datestart)
		date = information[datestart+5:dateend]
		whostart = information.find("Who=")
		whoend = information.find("\n", whostart)
		who = information[whostart+4:whoend]
		programstart = information.find("Program=")
		programend = information.find("\n", programstart)
		program = information[programstart+8:programend]
		timestart = information.find("Time=")
		timeend = information.find("\n", timestart)
		time = information[timestart+5:timeend]
		descriptionstart = information.find("Desc=")
		descriptionend = len(information)
		description = information[descriptionstart+5:descriptionend]
		durationstart = information.find("Length=")
		durationend = information.find("\n", durationstart)
		duration = information[durationstart+7:durationend]
		gracestart = information.find("Grace=")
		if gracestart == -1:
			grace = "Short"
		else:
			graceend = information.find("\n", gracestart)
			grace = information[gracestart+6:graceend]
		host = ctx.author.mention
		playerstart = information.find("Player=")
		if playerstart == -1:
			player = "5"
		else:
			playerend = information.find("\n", playerstart)
			player = information[playerstart+7:playerend]

		desc = f"\n**Date:** {date}\n**Time:** {time} EST\n**Length:** {duration}\n**Host:** {host}\n**Who:** {who}\n**Program:** {program}\n**Description:** {description}"

		if len(desc) > 2000:
			await ctx.channel.send(f"{host}\nThe message has a maximum of 2000 characters. You are currently at {len(desc)}")
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
				sheet_activesession.append_row([f"{date} {time}", time, duration, ctx.author.nick, who, assignedemogi, description, str(ctx.author.id), str(questactive.id), f"{timeposted.month}/{timeposted.day}/{timeposted.year} {timeposted.hour}:{timeposted.minute}", player], value_input_option='USER_ENTERED', insert_data_option="INSERT_ROWS", table_range="A1")
				await questactive.add_reaction(assignedemogi)
				return
			if reaction.emoji.name == "Rejected":
				await try_delete(sendmsg)
				return





def setup(bot):
	bot.add_cog(session(bot))
	# Adds the Basic commands to the bot
	# Note: The "setup" function has to be there in every cog file
