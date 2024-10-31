# This module contains the functionality for Apple Bot
# Author: Steven Tra
# Date: 2024-09-24
import os
import discord
from discord import app_commands
from discord.app_commands import commands
from dotenv import load_dotenv
from loguru import logger

import sys

from admin.birthdays import enter_birthday
from minigames.gamble import Economy, setup_economy_commands
from minigames.more_gambling import setup_gambling_games
from minigames.jobs import setup_job_system
from minigames.fun import setup_fishing_commands

from admin.server_events import *
from utils.utils import *

load_dotenv()

# Discord.py token
TOKEN = os.environ["DISCORD_API_TOKEN"]
APPLE_SERVER = os.environ["APPLE_SERVER"]
UPDATES_CHANNEL = int(os.environ["UPDATES_CHANNEL_ID"])

# Instantiate the logger; we'll be using Loguru for our logging purposes!
logger.remove(0)
logger.add(sys.stdout, level="INFO")
logger.add("logs/AppleBot.log", level="INFO", rotation="0:00", retention="14 days")

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

    @bot.tree.command(name="create_event",
                      description="Create a scheduled server event",
                      guild=discord.Object(id=APPLE_SERVER))
    @app_commands.describe(name="The name of the event",
                           description="The description of the event",
                           start_date="The start date for the event",
                           start_time="The start time for the event (in your local timezone)",
                           duration_hours="How long the event will last (in hours)",
                           channel="(Optional) The voice channel in which the event will be held",
                           location="(Optional) The location where the event will be held")
    async def create_event_command(
        interaction: discord.Interaction,
        name: str,
        description: str,
        start_date: str,
        start_time: str,
        duration_hours: float = 1.0,
        channel: discord.VoiceChannel = None,
        location: str = None
    ):
        # Convert start and end times to datetimes
        times = convert_start_and_end_times(start_date, start_time, duration_hours)
        st = times["st"]
        et = times["et"]

        await create_server_event(interaction.guild,
                                  name, description, st, et, channel.id, location)

    @bot.tree.command(name="create_overwatch_6v6",
                      description="Create an Overwatch 6v6",
                      guild=discord.Object(id=APPLE_SERVER))
    @app_commands.describe(name= "(Optional) The name of the event",
                           description="(Optional) The description for the 6v6",
                           start_date="The start date for the 6v6",
                           start_time="The start time for the 6v6",
                           duration_hours="(Optional) How long the 6v6 will last (in hours)",
                           channel="(Optional) The voice channel the 6v6 will be in")
    async def create_overwatch_6v6(
            interaction: discord.Interaction,
            start_date: str,
            start_time: str,
            name: str = None,
            description: str = None,
            duration_hours: float = 2.0,
            channel: discord.VoiceChannel = None,
    ):

        # Convert start and end times to datetimes
        times = convert_start_and_end_times(start_date, start_time, duration_hours)
        st = times["st"]
        et = times["et"]

        event = overwatch_6v6s(st, start_date, start_time)
        name = name if name is not None else event["name"]
        description = description if description is not None else event["description"]
        channel_id = channel.id if channel is not None else int(event["channel"])
        cover_image = image_to_bytes("images/tracer banner 800x320.jpeg")


        await create_server_event(interaction.guild,
                                  name, description, st, et, channel_id, cover_image)
    @bot.event
    async def on_ready():
        """ Logs to the console that Apple Bot is ready to use.
        """
        logger.info("Apple Bot is ready!")
        economy = Economy("./data/gambleData.json")
        await setup_economy_commands(bot, economy, APPLE_SERVER)
        await setup_gambling_games(bot, economy, APPLE_SERVER)
        await setup_job_system(bot, economy, APPLE_SERVER)
        await setup_fishing_commands(bot, economy, APPLE_SERVER)
        await bot.tree.sync(guild=discord.Object(id=int(APPLE_SERVER)))

        # If the bot was stopped previously, fetch the scheduled events for the server and create reminder messages that
        # will be sent at the specified reminder times

        for guild in bot.guilds:
            events = await guild.fetch_scheduled_events()
            if events:
                # Find the upcoming events which need reminder messages sent out and schedule them to be sent
                for event in events:
                    roles_to_ids = get_roles_to_ids(event)
                    updates_channel = bot.get_channel(UPDATES_CHANNEL)
                    await schedule_reminders(event, roles_to_ids, updates_channel)

    @bot.event
    async def on_scheduled_event_create(event: discord.ScheduledEvent):
        await on_event_create(bot, event)

    @bot.event
    async def on_message(message):
        await enter_birthday(bot, message)

    bot.run(TOKEN)
    logger.info("Apple Bot is shutting down...")