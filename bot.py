# This module contains the functionality for Apple Bot
# Author: Steven Tra
# Date: 2024-09-24

import random
from dotenv import load_dotenv
from loguru import logger
from datetime import date, datetime, timedelta

import os
import json
import sys
import numpy as np
import discord
import requests
import asyncio
import re
import pytz
from gamble import Economy, setup_economy_commands

from discord.ext import commands
from discord.utils import get

load_dotenv()

# Discord.py token
TOKEN = os.environ["DISCORD_API_TOKEN"]
headers = {"authorization": "Bot " + TOKEN}
TIMEZONE = os.environ["TIMEZONE"]
# The ID of the primary admin of the server; this member will input birthdays into the Birthday Bot
server_admin_ID = os.environ["DISCORD_SERVER_ADMIN_ID"]
apple_server = os.environ["APPLE_SERVER"]
bday_for_verification_channel_ID = int(os.environ["BDAY_FOR_VERIFICATION_CHANNEL_ID"])
commands_channel_ID = int(os.environ["COMMANDS_CHANNEL_ID"])
updates_channel_ID = int(os.environ["UPDATES_CHANNEL_ID"])
minor_role_ID = int(os.environ["MINOR_ROLE_ID"])
adult_role_ID = int(os.environ["ADULT_ROLE_ID"])
# Some servers may require a minimum age to be admitted; you may set that as an environment variable
minimum_age = int(os.environ["MINIMUM_AGE"])
# The list which defines when and how many times users should be reminded about the event before the event. Each entry
# in the list represents how many minutes before the event the user should be reminded about the current event that was
# scheduled.
reminder_times = np.array(json.loads(os.environ["REMINDER_TIMES"]), dtype="float")

# Instantiate the logger; we'll be using Loguru for our logging purposes!
logger.remove(0)
logger.add(sys.stdout, level="TRACE")
logger.add("logs/AppleBot.log", level="TRACE", rotation="0:00", retention="14 days")

def calculate_age(born : datetime):
    """Calculate the age of the user.

    :param born: the birthdate of the user
    :type born: datetime
    :return: the age of the user (in years)
    """
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

async def add_age_role(is_adult, message):
    """ Adds the appropriate age role to the user who enters their birthday into the bday-for-verification channel.

    :param is_adult: A boolean which is True if the user is at least 18 years of age and false otherwise
    :param message: The original message that was sent to the bday-for-verification channel
    """
    role_to_add = discord.utils.get(message.guild.roles, id=adult_role_ID) if is_adult \
        else discord.utils.get(message.guild.roles, id=minor_role_ID)
    role_to_remove = minor_role_ID if is_adult else adult_role_ID

    username = str(message.author)

    # If the user has the "Minor" role, remove it before adding the "Adult" role
    if role_to_remove in [role.id for role in message.author.roles]:
        logger.info(f"User {username} was previously assigned the wrong age role, removing it...")
        requests.delete(f"https://discord.com/api/guilds/{message.guild.id}/members/{message.author.id}/roles/{role_to_remove}",
                        headers=headers)

    await message.author.add_roles(role_to_add)

    if is_adult:
        logger.info(f"User {username} is an adult, assigning them the \"Adult\" role")
    else:
        logger.info(f"User {username} is a minor, assigning them the \"Minor\" role")

async def wait_until(dt, tzinfo):
    """Wait until the specified datetime.

    :param dt: This function will sleep until this datetime
    :param tzinfo: The timezone info for the datetime
    """
    # sleep until the specified datetime
    now = datetime.now(tzinfo)
    await asyncio.sleep((dt - now).total_seconds())

async def run_at(dt, tzinfo, coro):
    """Runs a coroutine at the specified time.

    :param dt: Datetime to run the coroutine at
    :param tzinfo: The timzeone info for the datetime
    :param coro: The coroutine to run at the datetime
    :return: The awaited coroutine
    """
    await wait_until(dt, tzinfo)
    return await coro

def get_roles_to_ids(event):
    """ Maps the role names (as strings) to their corresponding role IDs (as integers) and returns the
    resulting dictionary.

    :param event: The ScheduledEvent that we are pulling roles from the description
    :return: A dictionary that maps role names (as strings) to their corresponding role IDs (as integers)
    """
    # Get the roles that were mentioned in the description of the channel
    role_names = re.findall("@\w+", event.description)
    roles_to_ids = {}
    # Find the role IDs for each role mentioned and replace the text in the description
    for name in role_names:
        role_id = get(event.guild.roles, name=name[1:]).id  # Remove the "@" at the beginning of the name
        logger.debug(f"Role {name[1:]} id is {role_id}")
        roles_to_ids[name[1:]] = str(role_id)
    return roles_to_ids

async def create_reminder(event : discord.ScheduledEvent, minutes_before_event : int, role_ids : list, event_channel_id : int, channel_to_send):
    """Create a reminder message for the event and schedule it to be sent to the "updates" channel at the specified time
    before the event starts.

    :param event: The event to create the reminder for
    :param minutes_before_event: The number of minutes before the event starts
    :param role_ids: The list of role IDs that are mentioned in the message
    :param event_channel_id: The ID of the channel the event is happening in
    :param channel_to_send: The channel to send the reminder message in (usually "updates")
    """

    reminder_message = ""
    # Mention all the roles from the event description
    for role in role_ids:
        reminder_message += f"<@&{role}> "

    # If the event is not happening in a voice channel within the server, use the location instead
    event_location = f"{event.location}" if event_channel_id is None else f"<#{event_channel_id}>"

    if minutes_before_event > 0:
        minute_or_minutes = "minute" if minutes_before_event == 1 else "minutes"
        reminder_message += (f"**\"{event.name}\"** is starting in {int(minutes_before_event)} {minute_or_minutes}! Please come join us in "
                         f"{event_location} if you would like to participate! {event.url}")
    elif minutes_before_event == 0:
        reminder_message += (
            f"**\"{event.name}\"** is starting **RIGHT NOW!** Please come join us in "
            f"{event_location} if you would like to participate! {event.url}")

    logger.debug(reminder_message)

    event_tzinfo = event.start_time.tzinfo
    event_reminder = event.start_time - timedelta(minutes=minutes_before_event)

    logger.debug(f"Scheduling reminder message for \"{event.name}\" {int(minutes_before_event)} minutes before the event...")
    await run_at(event_reminder, event_tzinfo, channel_to_send.send(reminder_message))

async def schedule_reminders(event, roles_to_ids, updates_channel):
    """ Schedules reminder messages to be sent out to the specified updates channel. These reminder messages will be
    sent at the designated times before the event start time, and that is determined by the global reminder_times array.
    It will ignore any reminder times that are in the past.

    :param event: The ScheduledEvent to send reminders for
    :param roles_to_ids: The dictionary that maps role names (as strings) to role IDs (as integers)
    :param updates_channel: The updates channel in which the bot will send the reminders to
    """
    tz = pytz.timezone(TIMEZONE)
    current_time = datetime.now(tz=tz)
    minute_diff_event = (event.start_time - current_time).total_seconds() / 60
    if minute_diff_event >= 0:
        logger.debug(f"It is currently {current_time} UTC. The event titled \"{event.name}\" "
                     f"is starting in {minute_diff_event} minutes.")

        # Get all of the reminder times that are less than the current time diff and schedule reminder
        # messages for those times
        reminders = reminder_times[reminder_times < minute_diff_event]

        # Set the reminder times for the event by creating reminder functions with the parameters already set.
        # Store these reminder functions in a list which will then by called asynchronously

        reminder_functions = []
        for minutes_until in reminders:
            reminder_functions.append(create_reminder(event, minutes_until, list(roles_to_ids.values()),
                                                  event.channel_id, updates_channel))

        # Schedule the reminders
        await asyncio.gather(*reminder_functions)

def run_discord_bot():
    """The main function for running the discord bot. It triggers when a user types in the "bday-for-verification"
    channel. First, check to see if the user typed in a valid date (which will be validated via regular expressions).
    Second, parse the provided date and calculate the user's age. If the user is 18 or over, assign them the "18+" role;
    if they are under 18, it will assign them the "Minor" role. Lastly, it will add the birthday they provided to our
    Birthday Bot in the server.
    """

    intents = discord.Intents.all()
    intents.message_content = True
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.command(pass_context=True)
    async def addrole(ctx, user: discord.Member):
        """Adds a role to the specified user.

        :param ctx: The context in which the command is being invoked
        :param user: The user to add the role to
        """
        member = ctx.message.author
        role = get(member.server.roles, name="Test")
        await bot.add_roles(member, role)

    @bot.event
    async def on_ready():
        """ Logs to the console that Apple Bot is ready to use.
        """

        logger.info("Apple Bot is ready!")
        economy = Economy("./data/gambleData.json")
        await setup_economy_commands(bot, economy, apple_server)
        await bot.tree.sync(guild=discord.Object(id="878771899612680243"))

        # Why? I feel as that this should grab like `@bot.command` ?

        # If the bot was stopped previously, fetch the scheduled events for the server and create reminder messages that
        # will be sent at the specified reminder times
        for guild in bot.guilds:
            events = await guild.fetch_scheduled_events()

            if events:
                # Find the upcoming events which need reminder messages sent out and schedule them to be sent
                for event in events:
                    roles_to_ids = get_roles_to_ids(event)
                    updates_channel = bot.get_channel(updates_channel_ID)

                    await schedule_reminders(event, roles_to_ids, updates_channel)



    @bot.event
    async def on_scheduled_event_create(event: discord.ScheduledEvent):
        """ Fires whenever a Discord server event is created. The bot constructs an announcement messsage which pings
        the specific roles that were mentioned in the description of the event. It sends the message in the specified
        updates channel, and then it creates scheduled reminder messages that will be sent to the updates channel as
        the event approaches. By default, reminder messages will be sent 60 and 30 minutes before the event
        respectively.

        :param event: The scheduled event in the Discord server
        """
        logger.debug(f"User {event.creator} created the event \"{event.name}\" at {event.start_time} {TIMEZONE}!")
        logger.debug(f"Description of event: {event.description}")

        # Get the roles that were mentioned in the description of the channel
        role_names = re.findall("@\w+", event.description)
        logger.debug(f"Role(s) mentioned for event: {role_names}")

        roles_to_ids = get_roles_to_ids(event)

        # Replace every role name in the description with its corresponding role ID so we can mention the roles in the
        # announcement
        event_description = "" if event.description is None else event.description
        redacted_desc = event_description
        for name in role_names:
            redacted_desc = redacted_desc.replace(name, "<@&" + roles_to_ids[name[1:]] + ">")

        # Append the url to the event to the announcement
        redacted_desc += f" {event.url}"

        # Send a message to the updates channel mentioning everyone and include the description as the message
        updates_channel = bot.get_channel(updates_channel_ID)

        message = f"Message sent to updates channel: {event_description}"
        logger.debug(message)

        await updates_channel.send(f"{redacted_desc}")

        await schedule_reminders(event, roles_to_ids, updates_channel)

    @bot.event
    async def on_message(message):
        """ Assigns the appropriate age role to members in the server and creates the command to add their birthdays to
        the Birthday Bot. First, this function will check the "bday-for-verification" channel for messages that contain
        a MM/DD/YYYY formatted date. Then, it will parse the date and calculate the member's age based on the date. If
        they are under the age of 18, it will assign them the "Minor" role. Otherwise, it will assign them the 18+ role.
        Lastly, it will format the parsed date and create a message that is sent to the private "commands" channel for
        a server moderator to manually enter into the Birthday Bot.

        :param message: A message coming in to one of the server's text channels
        """
        if message.author == bot.user:
            return

        author = message.author


        # If the message is not in the "bday-for-verification" channel, do nothing. We only want to respond to dates
        # posted in that channel.
        if message.channel.id != bday_for_verification_channel_ID:
            return

        logger.debug(f"Message sent: {message}")

        try:
            username = str(message.author)
            ctx = await bot.get_context(message)
            user_profile_picture = ctx.message.author.avatar.with_size(128)
            channel = str(message.channel)

            birth_date = str(message.content)

            date_format = '%m/%d/%Y'
            try:
                birth_date_obj = datetime.strptime(birth_date, date_format)
                logger.info(f"User {username} entered the date {birth_date} in the {channel} channel.")
            except Exception as e:
                logger.error(f"Could not parse date. Error: {e}")
                return

            # Calculate the age of the user. If they're 18 or over, give them the "18+" role.
            # If they're under 18, give them the "Minor" role.
            age = calculate_age(birth_date_obj)

            # Get the commands channel object to send the messages from the bot
            bday_for_verification_channel = bot.get_channel(bday_for_verification_channel_ID)
            if age < 0:
                logger.info(f"User {username} entered an invalid birthdate.")
                embedVar = discord.Embed(title="ERROR", description=f"Oops! You entered a birthdate that was in the "
                                                                    f"future. Please enter in a valid birthdate in "
                                                                    f"the {bday_for_verification_channel.name} channel."
                                                                    , color=0xFF5733)
                embedVar.add_field(name="Birthdate Entered", value=birth_date, inline=False)
                await bday_for_verification_channel.send("<@" + str(message.author.id) + ">")
                await bday_for_verification_channel.send(embed=embedVar)
                return
            elif age < minimum_age:
                logger.info(f"User {username} is {age} years old, too young to be in this server...")
                embedVar = discord.Embed(title="ALERT", description=f"Oops! It seems like you may be too young to be a "
                                                                    f"member of {message.guild.name}. The minimum age "
                                                                    f"to be in this server is {minimum_age}. A server "
                                                                    f"moderator may contact you shortly to resolve this "
                                                                    f"issue.", color=0xffff00)
                await bday_for_verification_channel.send("<@" + str(message.author.id) + ">")
                await bday_for_verification_channel.send(embed=embedVar)

                # Alert the server admin about the user who is too young to be in the server
                bot_alerts_channel = bot.get_channel(int(os.environ["BOT_ALERTS_CHANNEL_ID"]))
                embedVar = discord.Embed(title="ALERT", description=f"User {username} has entered in the "
                                                                    f"{bday_for_verification_channel.name} channel "
                                                                    f"that they are {age} years old, below the current "
                                                                    f"minimum age of {minimum_age}.", color=0xffff00)
                embedVar.set_thumbnail(url=user_profile_picture)
                await bot_alerts_channel.send("<@" + server_admin_ID + ">")
                await bot_alerts_channel.send(embed=embedVar)
                return
            elif age >= 18:
                is_adult = True
            else:
                is_adult = False

            logger.info(f"User {username} is {age} years old")
            await add_age_role(is_adult, message)

            # Now we will send an embedded message that displays the username of the user, their birthday, their age,
            # their role (either "Adult" or "Minor"), and the command that a moderator will need to input in order to
            # add their birthday to the bot.

            embedVar = discord.Embed(title="User", description=username, color=0xFF5733)

            embedVar.add_field(name="Birthdate", value=birth_date, inline=False)
            embedVar.add_field(name="Age", value=age, inline=False)
            if is_adult:
                embedVar.add_field(name="Role", value=f"{username} has been given the role: Adult!", inline=False)
            else:
                embedVar.add_field(name="Role", value=f"{username} has been given the role: Minor!", inline=False)

            command_birth_date = birth_date_obj.strftime("%d %B")
            command_to_run = f"/override set-birthday target:@{username} date:{command_birth_date}"
            logger.debug(f"The command to add {username}'s birthday to the Birthday Bot is {command_to_run}")
            embedVar.add_field(name="Command To Run", value=command_to_run, inline=False)

            # Get the commands channel object to send the messages from the bot
            commands_channel = bot.get_channel(commands_channel_ID)

            embedVar.set_thumbnail(url=user_profile_picture)
            await commands_channel.send("<@" + server_admin_ID + ">")
            await commands_channel.send(embed=embedVar)

        except Exception as e:
            logger.error(e)

    bot.run(TOKEN)
    logger.info("Apple Bot is shutting down...")