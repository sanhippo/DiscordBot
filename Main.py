import random
import discord
import gspread
import asyncio
import socket
import credentials
import math
import datetime

catoffset = 3
global running
running = 0

gc = gspread.service_account()

workbook = gc.open("Elantris Downtime")

Testing = credentials.Testing


if Testing == 0:
    token = credentials.BotToken  # Actual Token
    sheetactivites = workbook.worksheet("Downtime")
    sheetlog = workbook.worksheet("Log")
    sheetplayerinfo = workbook.worksheet("Player")
    sheetinfo = workbook.worksheet("Info")
    sheetstatus = workbook.worksheet("Status")
    statusidchan = 741786416773595238
    messageid = 741796531467845793

else:
    token = credentials.TestToken  # Test Token
    sheetactivites = workbook.worksheet("DowntimeTest")
    sheetlog = workbook.worksheet("Log")
    sheetplayerinfo = workbook.worksheet("PlayerTest")
    sheetinfo = workbook.worksheet("Info")
    sheetstatus = workbook.worksheet("Status")

client = discord.Client()

hostname = socket.gethostname()

class Activity:  # Class for Activity Type Contains all the activity Information and is update on start and $Update Cmd

    def __init__(self, name, column, style, expectedinputs, extrainfo, roll):
        self.name = name
        self.column = column + catoffset
        self.style = style
        self.expectedinputs = expectedinputs
        self.extrainfo = extrainfo
        self.roll = roll
        self.results = []

    def add_results(self, result):
        self.results.append(result)


class RollResults:

    def __init__(self, description, type, log, value, hoursused, amountconsumed, daysinjured):
        self.description = description
        self.type = type
        self.log = log
        self.value = value
        self.hoursused = hoursused
        self.amountconsumed = amountconsumed
        self.daysinjured = daysinjured
        self.val2 = 0

    def add_val(self, addvalue):
        self.val2 = addvalue


class Player:

    def __init__(self, name, hoursused, maxhours, injury, activityvalue):
        self.name = name
        self.hoursused = int(hoursused)
        self.maxhours = int(maxhours)
        self.injury = int(injury)
        self.activityvalue = int(activityvalue)
        self.hoursleft = self.maxhours - self.hoursused


def utc_to_local(utc_dt):  # Convert UTC Time from Discord to EDT Time for use in the google sheet
    return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)


def updatecategories():  # Updates the Activity List

    global ActivityList
    ActivityList = []  # Clears out the Activity List

    get_values = sheetactivites.batch_get(["A:ZZ"], major_dimension="Columns")  # Gets all the Google Sheet Information Based on Columns

    z = 0  # Sets to Row 0 for each new activity

    for x in range(1, len(get_values[0])):
        ActivityList.append(Activity(get_values[0][x][0], x, get_values[0][x][1], get_values[0][x][2], get_values[0][x][3], get_values[0][x][4]))

        for y in range(5, len(get_values[0][1])):
            ActivityList[z].add_results(get_values[0][x][y])

        z = z + 1

    return


def GetPlayerIndex(message, collumn):  # Determine What Player Is Making the Request Updates every request to get new data

    PlayerList = sheetplayerinfo.col_values(1)  # Get Player Data

    for x in range(len(PlayerList)):

        if message.author.nick == PlayerList[x]:  # If Player Found report the value
            sheetvalues = sheetplayerinfo.row_values(x+1)

            player = Player(sheetvalues[0], sheetvalues[1], sheetvalues[2], sheetvalues[3], sheetvalues[collumn])

            return player

    return False  # If no player found report an error


def GetCategory(message):  # Determine Which Category Was Called

    for x in range(len(ActivityList)):
        if message.content.startswith(ActivityList[x].name):
            return ActivityList[x]

    return False


async def GetValid(message, SelectedPlayer, SelectedCategory):
    global MessageContentSplit

    MessageContentSplit = message.content.split(" ")

    del MessageContentSplit[0]

    for x in range(len(SelectedCategory.expectedinputs)):

        if len(SelectedCategory.expectedinputs) != len(MessageContentSplit):

            return False, f"{message.author.mention} {message.content}\n Invalid Number of Parameters. {len(SelectedCategory.expectedinputs)} Expected."

        if SelectedCategory.expectedinputs[x].upper() == "I":
            if not RepresentsInt(MessageContentSplit[x]):
                return False, f"{message.author.mention} {message.content}\n Invalid Parameter ({MessageContentSplit[1]}) Should be a Number."
            MessageContentSplit[x] = int(MessageContentSplit[x])

        if SelectedCategory.expectedinputs[x].upper() == "S":
            MessageContentSplit[x] = MessageContentSplit[x].upper()


    if ((MessageContentSplit[0] > SelectedPlayer.maxhours) or (MessageContentSplit[0] <= 0)):
        return False, f"{message.author.mention} {message.content}\n Invalid Hour Entry, Must Be Between 1 and {SelectedPlayer.hoursleft}"    # Invalid Hour Entry

    if MessageContentSplit[0] > SelectedPlayer.hoursleft:
        return False, f"{message.author.mention} {message.content}\n Not Enough Hours Left In Day, Hours Left: {SelectedPlayer.hoursleft}" # Not Enough Hours Left In the Day

    if SelectedPlayer.activityvalue == 0:
        return False, f"{message.author.mention} {message.content}\n Character Does Not Meet Requirements" # Character Does Not Meet Activity Requirements

    if (SelectedCategory.style.find("c") != -1):

        workamount = SelectedPlayer.activityvalue * MessageContentSplit[0]

        fstart = SelectedCategory.style.find("c,")
        fend = SelectedCategory.style.find(":", fstart)
        in_stock = float(sheetinfo.acell(SelectedCategory.extrainfo[fstart+3:fend]).value)

        if workamount > in_stock:
            MessageContentSplit[0] = math.floor(in_stock / SelectedPlayer.activityvalue)
            workamount == SelectedPlayer.activityvalue * MessageContentSplit[0]

            if MessageContentSplit[0] == 0:
                return False, f"{message.author.mention} {message.content}\nNot Enough Supplies. In Stock: {in_stock}"  # To Large of a Number Entered For Use

            await printdiscord(message, f"Not Enough Supplies, Hours Changed to {MessageContentSplit[0]}")

    if SelectedPlayer.injury != 0:
        if (SelectedCategory.style.find("i") == -1):
            return False, f"{message.author.mention} {message.content}\nInjured For {SelectedPlayer.injury} days. Can't Perform Selected Activity" # To Large of a Number Entered For Use

    return True, 0  # Return True For is a Valid Case


def RepresentsInt(s):
    try:
        int(s)

    except ValueError:
        return False
    return True


async def GetResult(message, SelectedPlayer, SelectedActivity):

    string_name_message = f"{message.author.mention} {message.content}\n"
    dice = SelectedActivity.roll.split("d")
    hoursleft = SelectedPlayer.hoursleft
    sheetdata = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # 0 = date
    # 1 = Time
    # 2 = Who
    # 3 = What
    # 4 = Log
    # 5 = Value
    # 6 = Used
    # 7 = Hours Used
    # 8 = Activity Name

    rolls = []
    totalroll = []

    for x in range(len(dice)):
        dice[x] = int(dice[x])

    for t in range(MessageContentSplit[0]):

        total = 0
        roll_values = []
        daysinjured = 0

        for x in range(dice[0]):
            roll_values.append(random.randint(1, dice[1]))
            total = total + roll_values[x]

        totalroll.append(total)

        sdescription = SelectedActivity.results[total-1]

        status_split = sdescription.split(":")

        status_split[1] = int(status_split[1])  # Type Number Increment for each new item combo
        status_split[2] = int(status_split[2])  # 0 = No Log, 1 = Log
        if (SelectedActivity.style.find("d") != -1):
            value_split = status_split[3].split(",")
            status_split[3] = float(value_split[0])
        else:
            status_split[3] = float(status_split[3])  # Value
        status_split[4] = int(status_split[4])  # 0 = max hours of day left

        if status_split[4] != 0:
            daysinjured = status_split[4]

        if (SelectedActivity.style.find("c") != -1):
            value = status_split[3] * SelectedPlayer.activityvalue
            rolls.append(RollResults(status_split[0], status_split[1], status_split[2], value, 1, SelectedPlayer.activityvalue, daysinjured))
        else:
            value = status_split[3]
            rolls.append(RollResults(status_split[0], status_split[1], status_split[2], value, 1, 0, daysinjured))

        if (SelectedActivity.style.find("d") != -1):
            rolls[t].add_val(float(value_split[1]))

        if daysinjured != 0:
            break

    combined_results = []

    for x in range(len(rolls)):
        if len(combined_results) == 0:
            combined_results.append(rolls[x])

        else:
            matchfound = 0

            for y in range(len(combined_results)):

                if rolls[x].type == combined_results[y].type:
                    matchfound = 1
                    combined_results[y].value = combined_results[y].value + rolls[x].value
                    combined_results[y].hoursused = combined_results[y].hoursused + rolls[x].hoursused
                    combined_results[y].amountconsumed = combined_results[y].amountconsumed + rolls[x].amountconsumed
                    combined_results[y].daysinjured = combined_results[y].daysinjured + rolls[x].daysinjured
                    combined_results[y].val2 = combined_results[y].val2 + rolls[x].val2

                    break

            if matchfound == 0:
                combined_results.append(rolls[x])

    for x in range(len(combined_results)):
        combined_results[x].value = round(combined_results[x].value)
        combined_results[x].val2 = round(combined_results[x].val2)

    msgesttime = utc_to_local(message.created_at)

    sheetdata[0] = (str(msgesttime.date()))  # Date
    sheetdata[1] = (str(msgesttime.time()))  # Time
    sheetdata[2] = (str(message.author.nick))  # Who
    sheetdata[8] = SelectedActivity.name  # Activity Name

    outputstring = string_name_message + f"\n**Rolls:** {totalroll}  \n**Hours Used - Results:**"


    for x in range(len(combined_results)):
        combined_results[x].description = combined_results[x].description.replace("{Value}", str(combined_results[x].value))

        if (SelectedActivity.style.find("c") != -1):

            combined_results[x].description = combined_results[x].description.replace("{Consumed}", str(combined_results[x].amountconsumed))
            sheetdata[6] = combined_results[x].amountconsumed  # Quantity used
        else:
            sheetdata[6] = 0

        if (SelectedActivity.style.find("d") != -1):
            combined_results[x].description = combined_results[x].description.replace("{2}",
                                                                                      str(combined_results[x].val2))

        outputstring = outputstring + f"\n **[{combined_results[x].hoursused}] - ** {combined_results[x].description}"

        sheetdata[3] = combined_results[x].description  # what
        sheetdata[4] = combined_results[x].log  # log
        sheetdata[5] = combined_results[x].value  # Value
        sheetdata[7] = combined_results[x].hoursused  # hours used
        sheetdata[9] = combined_results[x].daysinjured

        if (SelectedActivity.style.find("g") != -1):
            async with message.channel.typing():
                fstart = SelectedActivity.extrainfo.find("g,")
                fend = SelectedActivity.extrainfo.find(";", fstart)
                fstring = SelectedActivity.extrainfo[fstart+2:fend]
                fsplit = fstring.split("|")
                fbegin = (sheetinfo.acell(fsplit[0]).value)
                sheetlog.append_row(sheetdata, value_input_option='USER_ENTERED', insert_data_option="INSERT_ROWS",
                                    table_range="A1")
                x = 0
                while x < 15:
                    fcurrent = (sheetinfo.acell(fsplit[0]).value)
                    if fcurrent == fbegin:
                        await asyncio.sleep(1)
                        x += 1
                    else:
                        break

            fsplit[1] = fsplit[1].replace("{Value}", fcurrent)
            outputstring = outputstring + "\n" + fsplit[1]
        else:
            sheetlog.append_row(sheetdata, value_input_option='USER_ENTERED', insert_data_option="INSERT_ROWS",
                                table_range="A1")

    return outputstring


def getRoll(roll):

    dice = roll.split("d")

    for x in range(len(dice)):
        dice[x] = int(dice[x])

    total = 0
    roll_values = []

    for x in range(dice[0]):
        roll_values.append(random.randint(1, dice[1]))
        total = total + roll_values[x]

    return total, roll_values


def auth_and_chan(ctx):
    """Message check: same author and channel"""

    def chk(msg):
        return ctx.author == msg.author and ctx.channel == msg.channel

    return chk


async def townstatus():
    get_status = sheetstatus.batch_get(["A:C"], major_dimension="Columns")

    send_string = ""
    x = 1

    while x < len(get_status[0][0]):

        if not get_status[0][2][x] == "3":
            send_string = send_string + "\n"
        if get_status[0][2][x] == "0":
            send_string = send_string + (get_status[0][1][x])

        elif get_status[0][2][x] == "1":
            tempstring = get_status[0][1][x]
            tempstring = tempstring.replace("{Value}", get_status[0][0][x])
            send_string = send_string + tempstring

        x += 1

    return send_string


async def printdiscord(ctx, string):
    await ctx.channel.send(string)
    return

global ActivityList


async def waittime(seconds):

    while seconds > 86400:

        await asyncio.sleep(86400)
        seconds = seconds - 86400

    await asyncio.sleep(seconds)

    return


async def extracommands(ctx):

    if ctx.content == ("$Host"):
        if not (await check_cred(ctx, "Developer")):
            return 1
        await ctx.author.send(hostname)
        return 1

    if ctx.content.startswith("$Emote"):

        if not (await check_cred(ctx, "DM")):
            return 1
        await ctx.delete()
        fstart = ctx.content.find("[")
        fend = ctx.content.find("]", fstart)
        name = ctx.content[fstart + 1:fend]
        txt = ctx.content[fend + 2:]
        fstring = f"__**{name}**__ ```bash\n \"{txt}\" ```"
        await ctx.channel.send(fstring)
        return 1

    if ctx.content.startswith("$Update"):
        if not (await check_cred(ctx, "Developer")):
            return 1

        updatecategories()

        if ctx.content.startswith("$Update 1"):
            for x in range(len(ActivityList)):
                messagetosend = f"Name: {ActivityList[x].name}"
                await ctx.channel.send(messagetosend)

        await ctx.channel.send(f"{ctx.author.mention}\n List Updated")
        return 1

    if ctx.content.startswith("$Exit"):
        if not (await check_cred(ctx, "Developer")):
            return 1

        exit()

    if ctx.content == ("$SupplyUpdater"):
        if not (await check_cred(ctx, "Developer")):
            return 1
        await SupplyUpdater(ctx)
        return 1

    if ctx.content.startswith("$Roll"):
        dice = ctx.content.split(" ")

        results = getRoll(dice[1])

        sendstring = f"{ctx.author.mention}\n Rolls: {results[1]}\n Total: {results[0]}"
        await ctx.channel.send(sendstring)

        return 1

    if ctx.content == ("$Status"):
        await ctx.delete()
        tstatus = await townstatus()
        await ctx.author.send(tstatus)
        return 1

    return 0


async def check_cred(ctx, role):
    """Message check: Check To See if User has Correct Role"""
    for x in ctx.author.roles:
        if str(x) == role:
            return 1
    await ctx.author.send(f"You need the role {role} for this function.")
    return 0


async def SupplyUpdater(ctx):
    global running

    if not (await check_cred(ctx, "Developer")):
        return

    if running == 0:
        running = 1
        await ctx.channel.send("Running Wait Task")
        channelstatus = client.get_channel(statusidchan)
        editmessage = await channelstatus.fetch_message(messageid)
        await editmessage.edit(content=(await townstatus()))
    else:
        await ctx.channel.send("Running Wait Task Ended")
        running = 0

    while running == 1:
        await waittime(3600)
        await editmessage.edit(content=(await townstatus()))

    return

updatecategories()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):

    if message.author == client.user:
        return

    if message.content.startswith("$"):
        message.content = message.content[:1] + message.content[1].upper() + message.content[2:]
        ctx = message

        if await extracommands(ctx):
            return

        if message.content.startswith("$Test"):
            ctx = message

            if not (await check_cred(ctx, "Developer")):
                return

            await message.channel.send("Please Select From Options:")
            try:
                reply = await client.wait_for('message', timeout=30, check=lambda m: auth_and_chan(ctx)(m))
                if (not reply) or (not reply.content == "Yes, I am sure"):
                    await message.channel.send("Unconfirmed. Aborting.")
            except asyncio.TimeoutError:
                await message.channel.send("Unconfirmed. Aborting.")

            channel = message.channel

            await channel.send("Say Hello!")

            def check(m):
                return m.content == 'hello' and m.channel == channel

            try:
                await asyncio.wait_for(check(message), timeout=5.0)
            except asyncio.TimeoutError:
                print('timeout!')

            return

        if message.content.startswith("$"):

            SelectedActivity = GetCategory(message)

            if not SelectedActivity:
                await message.channel.send(f"{message.author.mention} {message.content}\n Activity {message.content} Not Found")
                return

            SelectedPlayer = GetPlayerIndex(message, SelectedActivity.column)

            if SelectedPlayer == False:
                await message.channel.send(f"{message.author.mention} {message.content}\n User {message.author.nick} Not Found!")
                return


            IsValid = await GetValid(message, SelectedPlayer, SelectedActivity)

            if not IsValid[0]:
                await message.channel.send(IsValid[1])
                return

            Result = await GetResult(message, SelectedPlayer, SelectedActivity)

            await message.channel.send(Result)

            return


client.run(token)