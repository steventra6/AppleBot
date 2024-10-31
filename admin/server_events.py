import os
import json

import dateparser
import discord
import pytz
import asyncio
import numpy as np
import re

from discord import PrivacyLevel
from loguru import logger
from datetime import datetime, timedelta
from utils.utils import run_at, get_roles_to_ids
from discord.ext import commands


TIMEZONE = os.environ["TIMEZONE"]
# The list which defines when and how many times users should be reminded about the event before the event
reminder_times = np.array(json.loads(os.environ["REMINDER_TIMES"]), dtype="float")
UPDATES_CHANNEL_ID = int(os.environ["UPDATES_CHANNEL_ID"])

OVERWATCH_ROLE_ID = os.environ["OVERWATCH_ROLE_ID"]

def overwatch_6v6s(start_time: datetime, start_date_str: str, start_time_str: str):
    if start_date_str is None:
        logger.error("Start date cannot be None for the Overwatch 6v6s!")
        raise ValueError("Start date cannot be None for the Overwatch 6v6s!")
    elif start_time_str is None:
        logger.error("Start time cannot be None for the Overwatch 6v6s!")
        raise ValueError("Start time cannot be None for the Overwatch 6v6s!")

    event = {
        "name" : "Overwatch 6v6s!!",
        "description": f"<@&{OVERWATCH_ROLE_ID}> Hello everyone!\n\nWe'll be having some **Overwatch 6v6s** this **{start_date_str}** at **{start_time_str}!**\n\nHope to see you there, and good luck in all your Overwatch adventures!",
        "start_time": start_time,
        "channel": os.environ["OVERWATCH_CHANNEL_ID"],
        "cover_image": "https://cdn.discordapp.com/attachments/1192842437819912383/1300224403153354782/tracer_800x320.jpeg?ex=67200fd6&is=671ebe56&hm=7a7ce1c21154cbdb73076c5ec8e980ee4de524c2630f05016b72ce181b8adc22&"
    }
    return event

async def create_reminder(event: discord.ScheduledEvent, minutes_before_event: int, role_ids: list, event_channel_id: int, channel_to_send):
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

    logger.info(reminder_message)

    event_tzinfo = event.start_time.tzinfo
    event_reminder = event.start_time - timedelta(minutes=minutes_before_event)

    logger.info(f"Scheduling reminder message for \"{event.name}\" {int(minutes_before_event)} minutes before the event...")
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
        logger.info(f"It is currently {current_time} UTC. The event titled \"{event.name}\" "
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

async def on_event_create(bot: commands.Bot, event: discord.ScheduledEvent):
        """ Fires whenever a Discord server event is created. The bot constructs an announcement messsage which pings
        the specific roles that were mentioned in the description of the event. It sends the message in the specified
        updates channel, and then it creates scheduled reminder messages that will be sent to the updates channel as
        the event approaches. By default, reminder messages will be sent 60 and 30 minutes before the event
        respectively.

        :param event: The scheduled event in the Discord server
        """
        logger.info(f"User {event.creator} created the event \"{event.name}\" at {event.start_time} {TIMEZONE}!")
        logger.info(f"Description of event: {event.description}")

        # Get the roles that were mentioned in the description of the channel
        role_names = re.findall("@\w+", event.description)
        logger.info(f"Role(s) mentioned for event: {role_names}")

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
        updates_channel = bot.get_channel(UPDATES_CHANNEL_ID)

        message = f"Message sent to updates channel: {event_description}"
        logger.info(message)

        await updates_channel.send(f"{redacted_desc}")

        await schedule_reminders(event, roles_to_ids, updates_channel)


async def create_server_event(
        guild: discord.Guild,
        name: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        channel_id: int = None,
        cover_image: str = None,
        location: str = None
) -> discord.ScheduledEvent:
    """Creates a scheduled event in the Discord server.

    Args:
        guild: The Discord guild to create the event in
        name: Name of the event
        description: Description of the event
        start_time: When the event starts
        end_time: When the event ends
        channel_id: Optional voice channel ID for the event
        location: Optional external location for the event. Required if channel_id is None.

    Returns:
        The created ScheduledEvent

    Raises:
        ValueError: If neither channel_id nor location is provided, or if both are provided
    """
    if channel_id is None and location is None:
        error_msg = "Either channel_id or location must be provided"
        logger.error(error_msg)
        raise ValueError(error_msg)

    if channel_id is not None and location is not None:
        error_msg = "Cannot provide both channel_id and location"
        logger.error(error_msg)
        raise ValueError(error_msg)

    if channel_id:
        channel = guild.get_channel(channel_id)
        if not isinstance(channel, discord.VoiceChannel):
            error_msg = "Channel must be a voice channel"
            logger.error(error_msg)
            raise ValueError(error_msg)

        if cover_image is None:
             return await guild.create_scheduled_event(
                name=name,
                description=description,
                start_time=start_time,
                end_time=end_time,
                privacy_level=PrivacyLevel.guild_only,
                entity_type=discord.EntityType.voice,
                channel=channel)
        else:
            return await guild.create_scheduled_event(
                name=name,
                description=description,
                start_time=start_time,
                end_time=end_time,
                privacy_level=PrivacyLevel.guild_only,
                entity_type=discord.EntityType.voice,
                channel=channel,
                image=cover_image)
    else:
        return await guild.create_scheduled_event(
            name=name,
            description=description,
            start_time=start_time,
            end_time=end_time,
            entity_type=discord.EntityType.external,
            location=location
        )

def convert_start_and_end_times(start_date, start_time, duration_hours):
        st_date = dateparser.parse(start_date)
        st_time = dateparser.parse(start_time)
        st = datetime.combine(st_date, st_time.time(), st_time.tzinfo)
        dt = timedelta(hours=duration_hours)
        et = st + dt
        return { "st": st, "et": et}