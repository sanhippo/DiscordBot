import asyncio
import random
from itertools import zip_longest
import discord
from fuzzywuzzy import fuzz, process
from cogs.models.errors import NoSelectionElements, SelectionCancelled, NoNickFound, ActivityNotFound
import gspread
from gspread.models import Cell
import datetime


gc = gspread.service_account()

wdowntime = gc.open("Elantris Downtime")
sheetplayer = wdowntime.worksheet("Player")
sheetactivties = wdowntime.worksheet("DowntimeTest")
workbook = gc.open("Desolation Player Management")
sheet_managment = workbook.worksheet("Management")
sheet_all_characters = workbook.worksheet("Character")
sheet_alive_characters = workbook.worksheet("Character's Alive")


class playerinfo:

	def __init__(self, name, hoursused, maxhours, injury, activityvalue):
		self.name = name
		self.hoursused = int(hoursused)
		self.maxhours = int(maxhours)
		self.injury = int(injury)
		self.activityvalue = int(activityvalue)
		self.hoursleft = self.maxhours - self.hoursused


def list_get(index, default, l):
	try:
		a = l[index]
	except IndexError:
		a = default
	return a


def get_positivity(string):
	if isinstance(string, bool):  # oi!
		return string
	lowered = string.lower()
	if lowered in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
		return True
	elif lowered in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
		return False
	else:
		return None


def search(list_to_search: list, value, key, cutoff=5, return_key=False, strict=False):
	"""Fuzzy searches a list for an object
	result can be either an object or list of objects
	:param list_to_search: The list to search.
	:param value: The value to search for.
	:param key: A function defining what to search for.
	:param cutoff: The scorer cutoff value for fuzzy searching.
	:param return_key: Whether to return the key of the object that matched or the object itself.
	:param strict: If True, will only search for exact matches.
	:returns: A two-tuple (result, strict)"""
	# there is nothing to search
	if len(list_to_search) == 0:
		return [], False

	# full match, return result
	exact_matches = [a for a in list_to_search if value.lower() == key(a).lower()]
	if not (exact_matches or strict):
		partial_matches = [a for a in list_to_search if value.lower() in key(a).lower()]
		if len(partial_matches) > 1 or not partial_matches:
			names = [key(d).lower() for d in list_to_search]
			fuzzy_map = {key(d).lower(): d for d in list_to_search}
			fuzzy_results = [r for r in process.extract(value.lower(), names, scorer=fuzz.ratio) if r[1] >= cutoff]
			fuzzy_sum = sum(r[1] for r in fuzzy_results)
			fuzzy_matches_and_confidences = [(fuzzy_map[r[0]], r[1] / fuzzy_sum) for r in fuzzy_results]

			# display the results in order of confidence
			weighted_results = []
			weighted_results.extend((match, confidence) for match, confidence in fuzzy_matches_and_confidences)
			weighted_results.extend((match, len(value) / len(key(match))) for match in partial_matches)
			sorted_weighted = sorted(weighted_results, key=lambda e: e[1], reverse=True)

			# build results list, unique
			results = []
			for r in sorted_weighted:
				if r[0] not in results:
					results.append(r[0])
		else:
			results = partial_matches
	else:
		results = exact_matches

	if len(results) > 1:
		if return_key:
			return [key(r) for r in results], False
		else:
			return results, False
	elif not results:
		return [], False
	else:
		if return_key:
			return key(results[0]), True
		else:
			return results[0], True


async def search_and_select(ctx, list_to_search: list, query, key, cutoff=5, return_key=False, pm=False, message=None,
							list_filter=None, selectkey=None, search_func=search, return_metadata=False):
	"""
	Searches a list for an object matching the key, and prompts user to select on multiple matches.
	:param ctx: The context of the search.
	:param list_to_search: The list of objects to search.
	:param query: The value to search for.
	:param key: How to search - compares key(obj) to value
	:param cutoff: The cutoff percentage of fuzzy searches.
	:param return_key: Whether to return key(match) or match.
	:param pm: Whether to PM the user the select prompt.
	:param message: A message to add to the select prompt.
	:param list_filter: A filter to filter the list to search by.
	:param selectkey: If supplied, each option will display as selectkey(opt) in the select prompt.
	:param search_func: The function to use to search.
	:param return_metadata Whether to return a metadata object {num_options, chosen_index}.
	:return:
	"""
	if list_filter:
		list_to_search = list(filter(list_filter, list_to_search))

	if search_func is None:
		search_func = search

	if asyncio.iscoroutinefunction(search_func):
		result = await search_func(list_to_search, query, key, cutoff, return_key)
	else:
		result = search_func(list_to_search, query, key, cutoff, return_key)

	if result is None:
		raise NoSelectionElements("No matches found.")
	strict = result[1]
	results = result[0]

	if strict:
		result = results
	else:
		if len(results) == 0:
			raise NoSelectionElements()

		first_result = results[0]
		confidence = fuzz.partial_ratio(key(first_result).lower(), query.lower())
		if len(results) == 1 and confidence > 75:
			result = first_result
		else:
			if selectkey:
				options = [(selectkey(r), r) for r in results]
			elif return_key:
				options = [(r, r) for r in results]
			else:
				options = [(key(r), r) for r in results]
			result = await get_selection(ctx, options, pm=pm, message=message, force_select=True)
	if not return_metadata:
		return result
	metadata = {
		"num_options": 1 if strict else len(results),
		"chosen_index": 0 if strict else results.index(result)
	}
	return result, metadata


def a_or_an(string, upper=False):
	if string.startswith('^') or string.endswith('^'):
		return string.strip('^')
	if re.match('[AEIOUaeiou].*', string):
		return 'an {0}'.format(string) if not upper else f'An {string}'
	return 'a {0}'.format(string) if not upper else f'A {string}'


def camel_to_title(string):
	return re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', string).title()


def paginate(iterable, n, fillvalue=None):
	args = [iter(iterable)] * n
	return [i for i in zip_longest(*args, fillvalue=fillvalue) if i is not None]


async def get_selection(ctx, choices, delete=True, pm=False, message=None, force_select=False):
	"""Returns the selected choice, or None. Choices should be a list of two-tuples of (name, choice).
	If delete is True, will delete the selection message and the response.
	If length of choices is 1, will return the only choice unless force_select is True.
	:raises NoSelectionElements: if len(choices) is 0.
	:raises SelectionCancelled: if selection is cancelled."""
	if len(choices) == 0:
		raise NoSelectionElements()
	elif len(choices) == 1 and not force_select:
		return choices[0][1]

	page = 0
	pages = paginate(choices, 10)
	m = None
	selectMsg = None

	def chk(msg):
		valid = [str(v) for v in range(1, len(choices) + 1)] + ["c", "n", "p"]
		return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.lower() in valid

	for n in range(200):
		_choices = pages[page]
		names = [o[0] for o in _choices if o]
		embed = discord.Embed()
		embed.title = "Multiple Matches Found"
		selectStr = "Which one were you looking for? (Type the number or \"c\" to cancel)\n"
		if len(pages) > 1:
			selectStr += "`n` to go to the next page, or `p` for previous\n"
			embed.set_footer(text=f"Page {page + 1}/{len(pages)}")
		for i, r in enumerate(names):
			selectStr += f"**[{i + 1 + page * 10}]** - {r}\n"
		embed.description = selectStr
		embed.colour = random.randint(0, 0xffffff)
		if message:
			embed.add_field(name="Note", value=message, inline=False)
		if selectMsg:
			try:
				await selectMsg.delete()
			except:
				pass
		if not pm:
			selectMsg = await ctx.channel.send(embed=embed)
		else:
			embed.add_field(name="Instructions",
							value="Type your response in the channel you called the command. This message was PMed to "
								  "you to hide the monster name.", inline=False)
			selectMsg = await ctx.author.send(embed=embed)

		try:
			m = await ctx.bot.wait_for('message', timeout=30, check=chk)
		except asyncio.TimeoutError:
			m = None

		if m is None:
			break
		if m.content.lower() == 'n':
			if page + 1 < len(pages):
				page += 1
			else:
				await ctx.channel.send("You are already on the last page.")
		elif m.content.lower() == 'p':
			if page - 1 >= 0:
				page -= 1
			else:
				await ctx.channel.send("You are already on the first page.")
		else:
			break

	if delete and not pm:
		try:
			await selectMsg.delete()
			await m.delete()
		except:
			pass
	if m is None or m.content.lower() == "c":
		raise SelectionCancelled()
	return choices[int(m.content) - 1][1]


ABILITY_MAP = {'str': 'Strength', 'dex': 'Dexterity', 'con': 'Constitution',
			   'int': 'Intelligence', 'wis': 'Wisdom', 'cha': 'Charisma'}


def verbose_stat(stat):
	return ABILITY_MAP[stat.lower()]


async def confirm(ctx, message, delete_msgs=False):
	"""
	Confirms whether a user wants to take an action.
	:rtype: bool|None
	:param ctx: The current Context.
	:param message: The message for the user to confirm.
	:param delete_msgs: Whether to delete the messages.
	:return: Whether the user confirmed or not. None if no reply was recieved
	"""
	msg = await ctx.channel.send(message)
	try:
		reply = await ctx.bot.wait_for('message', timeout=30, check=auth_and_chan(ctx))
	except asyncio.TimeoutError:
		return None
	replyBool = get_positivity(reply.content) if reply is not None else None
	if delete_msgs:
		try:
			await msg.delete()
			await reply.delete()
		except:
			pass
	return replyBool


async def getinput(ctx, message, delete_msgs=True, time=30):
	"""
	Confirms whether a user wants to take an action.
	:rtype: string
	:param ctx: The current Context.
	:param message: The message for the user to confirm.
	:param delete_msgs: Whether to delete the messages.
	:return: Whether the user confirmed or not. None if no reply was recieved
	"""
	msg = await ctx.channel.send(message)

	try:
		reply = await ctx.bot.wait_for('message', timeout=time, check=auth_and_chan(ctx))
	except asyncio.TimeoutError:
		if delete_msgs:
			try:
				await msg.delete()
				await reply.delete()
			except:
				pass
		return None
	replystring = reply.content
	if delete_msgs:
		try:
			await msg.delete()
			await reply.delete()
		except:
			pass
	return replystring


async def try_delete(message):
	try:
		await message.delete()
	except discord.HTTPException:
		pass


def maybe_mod(val: str, base=0):
	"""
	Takes an argument, which is a string that may start with + or -, and returns the value.
	If *val* starts with + or -, it returns *base + val*.
	Otherwise, it returns *val*.
	"""
	base = base or 0

	try:
		if val.startswith(('+', '-')):
			base += int(val)
		else:
			base = int(val)
	except (ValueError, TypeError):
		return base
	return base


def bubble_format(value: int, max_: int, fill_from_right=False):
	"""Returns a bubble string to represent a counter's value."""
	if max_ > 100:
		return f"{value}/{max_}"

	used = max_ - value
	filled = '\u25c9' * value
	empty = '\u3007' * used
	if fill_from_right:
		return f"{empty}{filled}"
	return f"{filled}{empty}"


def long_source_name(source):
	return constants.SOURCE_MAP.get(source, source)


def source_slug(source):
	return constants.SOURCE_SLUG_MAP.get(source)


def natural_join(things, between: str):
	if len(things) < 3:
		return f" {between} ".join(things)
	first_part = ", ".join(things[:-1])
	return f"{first_part}, {between} {things[-1]}"


def trim_str(text, max_len):
	"""Trims a string to max_len."""
	if len(text) < max_len:
		return text
	return f"{text[:max_len - 4]}..."


async def user_from_id(ctx, the_id):
	"""
	Gets a :class:`discord.User` given their user id in the context. Returns member if context has data.
	:type ctx: discord.ext.commands.Context
	:type the_id: int
	:rtype: discord.User
	"""

	async def update_known_user(the_user):
		await ctx.bot.mdb.users.update_one(
			{"id": str(the_user.id)},
			{"$set": {'username': the_user.name, 'discriminator': the_user.discriminator,
					  'avatar': the_user.avatar, 'bot': the_user.bot}},
			upsert=True
		)

	if ctx.guild:  # try and get member
		member = ctx.guild.get_member(the_id)
		if member is not None:
			await update_known_user(member)
			return member

	# try and see if user is in bot cache
	user = ctx.bot.get_user(the_id)
	if user is not None:
		await update_known_user(user)
		return user

	# or maybe the user is in our known user db
	user_doc = await ctx.bot.mdb.users.find_one({"id": str(the_id)})
	if user_doc is not None:
		# noinspection PyProtectedMember
		# technically we're not supposed to create User objects like this
		# but it *should* be fine
		return discord.User(state=ctx.bot._connection, data=user_doc)

	# fetch the user from the Discord API
	try:
		fetched_user = await ctx.bot.fetch_user(the_id)
	except discord.NotFound:
		return None

	await update_known_user(fetched_user)
	return fetched_user


async def checkperm(ctx, crole, messageuser=True, message=None):
	"""
	Checks To see if the user has a specific role or is a devloper
	:type ctx: discord.ext.commands.Context
	:type crole: role to check for
	:rtype: bool
	"""
	for roles in ctx.message.author.roles:
		if (roles.name == crole) or (roles.name == "Developer"):
			return True
	if messageuser:
		if message is None:
			sendmessage = f"You need the Role: {crole} for this command!"
		else:
			sendmessage = message
		await ctx.author.send(message)
	return False


async def getplayer(ctx):
	"""
	Checks to See if the user is listed under active players
	:param ctx: context
	:return: Class of Player or None
	"""

	list_of_dicts = sheetplayer.get_all_records()

	for playerdata in list_of_dicts:

		if ctx.author.nick == playerdata['Names:']:
			return playerdata

	raise NoNickFound(ctx.author.nick)

ActivityArray = []


class Activity:  # Class for Activity Type Contains all the activity Information and is update on start and $Update Cmd

	def __init__(self, name, style, expectedinputs, extrainfo, roll):
		self.name = name
		self.style = style
		self.expectedinputs = expectedinputs
		self.extrainfo = extrainfo
		self.roll = roll
		self.results = []

	def add_results(self, count, result):
		resultsplit = result.split(":")
		description = resultsplit[0]
		category = resultsplit[1]
		log = resultsplit[2]
		calcval = resultsplit[3]
		hoursused = resultsplit[4]
		resultdict = dict(roll=count, description=description, category=category, log=log, calcval=calcval, hoursused=hoursused)

		self.results.append(resultdict)


async def updateactivity(ctx, printmsg=None):
	"""
	:param ctx: context
	:param printmsg: print out to command
	:return: True if completed, or None
	"""
	global ActivityArray
	ActivityArray = []

	get_values = sheetactivties.batch_get(["A:ZZ"], major_dimension="Columns")  # Gets all the Google Sheet Information Based on Columns

	z = 0  # Sets to Row 0 for each new activity

	for x in range(1, len(get_values[0])):
		ActivityArray.append(Activity(get_values[0][x][0], get_values[0][x][1], get_values[0][x][2], get_values[0][x][3], get_values[0][x][4]))

		for y in range(5, len(get_values[0][1])):
			ActivityArray[z].add_results(y-4, get_values[0][x][y])

		z = z + 1

	return True


async def getactivity(ctx, activity):
	"""
	Gets the activity list
	:param ctx: context
	:param activity: str of class
	:return: activity class or None
	"""
	global ActivityArray
	activity = activity.lower()

	if len(ActivityArray) == 0:
		await updateactivity(ctx)

	for activities in ActivityArray:
		if activities.name == activity:
			return activities

	await updateactivity(ctx)

	for activities in ActivityArray:
		if activities.name == activity:
			return activities

	raise ActivityNotFound(activity)


def update_character_data(character_data, rownumber, checkinfo_data=None):
	"""
	Gets the activity list
	:param Character_data: Dictionary of Character Data
	:param checkinfo_data: Dictionary to compare to
	:return: bool
	"""
	cells = []
	col = 1
	if checkinfo_data is None:
		for data in character_data:
			cells.append(Cell(row=rownumber, col=col, value=str(character_data[data])))
			col += 1
		sheet_all_characters.update_cells(cells, value_input_option="USER_ENTERED")
		return True
	else:
		False


async def waittime(seconds):

	while seconds > 86400:

		await asyncio.sleep(86400)
		seconds = seconds - 86400

	await asyncio.sleep(seconds)

	return


def update_rp_data(newinfo):
	"""
	Gets the activity list
	:param newinfo: Dictionary of ID and character counts
	:return: null
	"""
	cells = []
	col = 1
	batch_player_data = sheet_managment.get_all_records()

	for x in newinfo:
		rownumber = 2
		for y in batch_player_data:
			if y["DiscordID"] == x["id"]:
				cells.append(Cell(row=rownumber, col=3, value=str(x["count"]+y["rp_messages"])))
				break
			else:
				rownumber += 1

	sheet_managment.update_cells(cells, value_input_option="USER_ENTERED")
	return


def get_emoji(ctx, Search):
	"""
	Gets the activity list
	:param ctx: Contexts
	:param Search: Name of emoji to Look For
	:return: emoji or None
	"""
	for emoji in ctx.guild.emojis:
		if emoji.name == Search:
			return emoji
	return None


def auth_and_chan(ctx):
	"""Message check: same author and channel"""

	def chk(msg):
		return msg.author == ctx.author and msg.channel == ctx.channel

	return chk


def utc_to_local(utc_dt):  # Convert UTC Time from Discord to EDT Time for use in the google sheet
	return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)


async def emojiconfirm(self, where, sendmsg=""):
	sendmsg = sendmsg + f"\nReact with ✅ to accept\nReact with ❌ to reject."
	msg = await where.member.send(sendmsg)
	await msg.add_reaction("✅")
	await msg.add_reaction("🚫")

	def check(reaction, user):
		return user.id == where.user_id and (reaction.emoji == "✅" or reaction.emoji == "🚫")

	try:
		reaction, user = await self.bot.wait_for('reaction_add', timeout=120.0, check=check)
	except asyncio.TimeoutError:
		return -1
	if reaction.emoji == "✅":
		return True
	if reaction.emoji == "🚫":
		return False
	return -2


async def sendlong(where, message):
	length = len(message)
	x = 0
	length = length
	if length > 1999:
		finished = False
		while not finished:
			if x + 250 < length:
				findnewline = message[x:x+1999].rfind("\n")
				if findnewline == -1:
					await where.send(message[x:x+1999])
					x = x + 1999
				else:
					await where.send(message[x:x+findnewline])
					x = x + findnewline
			else:
				await where.send(message[x:length])
				finished = True
	else:
		await where.send(message)
	return


async def emojimulti(self, where, choices, title="", who=None, delete=True):
	"""

	:param self: Context for the bot
	:param where: where the message will be sent
	:param choices: a list of choices for the user to select from
	:param title: a message to include at the top of the message
	:param who: who is able to respond to the  message
	:param delete: if the message should be deleted
	:return: the choice selected or -1 if timedout
	"""
	if len(choices) == 0:
		return -1
	if len(choices) == 1:
		return choices[0]
	x = 0
	selected = None
	sendstringtitle = f"**{title}**\n__React with your choice.__\n"
	msg = await where.send("Message Being Edited Please Wait")
	one = False
	two = False
	three = False
	four = False
	five = False
	six = False
	seven = False
	eight = False
	nine = False
	left = False
	right = False
	while selected is None:
		if len(choices) > x:
			sendstringmsg = f":one: {choices[x]}\n"
		if len(choices) > x+1:
			sendstringmsg = sendstringmsg + f":two: {choices[x+1]}\n"
		if len(choices) > x+2:
			sendstringmsg = sendstringmsg + f":three: {choices[x+2]}\n"
		if len(choices) > x+3:
			sendstringmsg = sendstringmsg + f":four: {choices[x+3]}\n"
		if len(choices) > x+4:
			sendstringmsg = sendstringmsg + f":five: {choices[x+4]}\n"
		if len(choices) > x+5:
			sendstringmsg = sendstringmsg + f":six: {choices[x+5]}\n"
		if len(choices) > x+6:
			sendstringmsg = sendstringmsg + f":seven: {choices[x+6]}\n"
		if len(choices) > x+7:
			sendstringmsg = sendstringmsg + f":eight: {choices[x+7]}\n"
		if len(choices) > x+8:
			sendstringmsg = sendstringmsg + f":nine: {choices[x+8]}\n"
		if x > 0:
			sendstringmsg = sendstringmsg + "⬅ Previous Page\n"
		if len(choices) > x+9:
			sendstringmsg = sendstringmsg + "➡ Next Page\n"

		msgcontent = sendstringtitle + sendstringmsg


		await msg.edit(content=msgcontent)

		if len(choices) > x:
			if not one:
				await msg.add_reaction('1️⃣')
				one = True
		else:
			if one:
				await msg.remove_reaction('1️⃣', self.bot.user)
				one = False
		if len(choices) > x+1:
			if not two:
				await msg.add_reaction('2️⃣')
				second = True
		else:
			if two:
				await msg.remove_reaction('2️⃣', self.bot.user)
				two = False
		if len(choices) > x+2:
			if not three:
				await  msg.add_reaction('3️⃣')
				third = True
		else:
			if three:
				await msg.remove_reaction('3️⃣', self.bot.user)
				three = False
		if len(choices) > x+3:
			if not four:
				await msg.add_reaction('4️⃣')
				four = True
		else:
			if four:
				await msg.remove_reaction('4️⃣', self.bot.user)
				four = False
		if len(choices) > x+4:
			if not five:
				await msg.add_reaction('5️⃣')
				five = True
		else:
			if five:
				await msg.remove_reaction('5️⃣', self.bot.user)
				five = False
		if len(choices) > x+5:
			if not six:
				await msg.add_reaction('6️⃣')
				six = True
		else:
			if six:
				await msg.remove_reaction('6️⃣', self.bot.user)
				six = False
		if len(choices) > x+6:
			if not seven:
				await msg.add_reaction('7️⃣')
				seven = True
		else:
			if seven:
				await msg.remove_reaction('7️⃣', self.bot.user)
				seven = False
		if len(choices) > x+7:
			if not eight:
				await msg.add_reaction('8️⃣')
				eight = True
		else:
			if eight:
				await msg.remove_reaction('8️⃣', self.bot.user)
				eight = False
		if len(choices) > x+8:
			if not nine:
				await msg.add_reaction('9️⃣')
				nine = True
		else:
			if nine:
				await msg.remove_reaction('9️⃣', self.bot.user)
				nine = False
		if x > 0:
			if not left:
				await msg.add_reaction("⬅")
				left = True
		else:
			if left:
				await msg.remove_reaction('⬅', self.bot.user)
		if len(choices) > x+9:
			if not right:
				await msg.add_reaction("➡")
				right = True
		else:
			if right:
				await msg.remove_reaction("➡", self.bot.user)
				right = False

		def check(reaction, user):
			return user.id == who and reaction.message.channel.id == where.id

		try:
			reaction, user = await self.bot.wait_for('reaction_add', timeout=120.0, check=check)
		except asyncio.TimeoutError:
			return -1
		await msg.remove_reaction(reaction.emoji, user)
		if reaction.emoji == '1️⃣':
			selected = choices[x]
		elif reaction.emoji == '2️⃣':
			selected = choices[x+1]
		elif reaction.emoji == '3️⃣':
			selected = choices[x+2]
		elif reaction.emoji == '4️⃣':
			selected = choices[x+3]
		elif reaction.emoji == '5️⃣':
			selected = choices[x+4]
		elif reaction.emoji == '6️⃣':
			selected = choices[x+5]
		elif reaction.emoji == '7️⃣':
			selected = choices[x+6]
		elif reaction.emoji == '8️⃣':
			selected = choices[x+7]
		elif reaction.emoji == '9️⃣':
			selected = choices[x+8]
		elif reaction.emoji == "⬅":
			x = x - 9
		elif reaction.emoji == "➡":
			x = x + 9
	if delete:
		await try_delete(msg)
	return selected


def getcharacters(discordid, dead=False, what="All"):
	if dead:
		batch_character_list = sheet_all_characters.get_all_records()
	else:
		batch_character_list = sheet_alive_characters.get_all_records()
	if len(batch_character_list) < 1:
		return None
	characterlist = []
	for character in batch_character_list:
		if character["DiscordID"] == discordid:
			if what == "All":
				characterlist.append(character)
			else:
				characterlist.append(character[what])
	if len(characterlist) < 1:
		return None
	return characterlist
