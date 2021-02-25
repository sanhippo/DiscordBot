from discord.ext import commands
import datetime
import d20
import gspread
from utils.functions import checkperm, get_emoji, try_delete, utc_to_local
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
		if payload.member.bot:
			return
		if payload.channel_id != questid:
			return
		#  Add Code here to Delete

		batch_get_signups = sheet_signups.get_all_records()
		batch_get_joinlist = sheet_joinlist.get_all_records()
		if len(batch_get_signups) > 0:
			for signups in batch_get_signups:
				if signups["Character"] == payload.member.nick:
					if signups["Assignment"] == payload.emoji.name:
						await payload.member.send(f"You are already signed up for session {payload.emoji.name}.")
						return
		timeposted = datetime.datetime.now()
		sheet_signups.append_row([f"{timeposted.month}/{timeposted.day}/{timeposted.year} {timeposted.hour}:{timeposted.minute}:{timeposted.second}:{timeposted.microsecond}", payload.emoji.name, payload.member.nick, str(payload.message_id), str(payload.user_id)], value_input_option='USER_ENTERED', insert_data_option="INSERT_ROWS", table_range="A1")
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
				sheet_activesession.append_row([f"{date} {time}", time, duration, ctx.author.nick, who, assignedemogi, description, str(ctx.author.id), str(questactive.id), f"{timeposted.month}/{timeposted.day}/{timeposted.year} {timeposted.hour}:{timeposted.minute}"], value_input_option='USER_ENTERED', insert_data_option="INSERT_ROWS", table_range="A1")
				await questactive.add_reaction(assignedemogi)
				return
			if reaction.emoji.name == "Rejected":
				await try_delete(sendmsg)
				return





def setup(bot):
	bot.add_cog(session(bot))
	# Adds the Basic commands to the bot
	# Note: The "setup" function has to be there in every cog file
