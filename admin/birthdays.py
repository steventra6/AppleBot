from dotenv import load_dotenv

import os
import discord
import requests
from datetime import date, datetime
from loguru import logger

load_dotenv()

BDAY_FOR_VERIFICATION_CHANNEL_ID = int(os.environ["BDAY_FOR_VERIFICATION_CHANNEL_ID"])
SERVER_ADMIN_ID = os.environ["DISCORD_SERVER_ADMIN_ID"]
COMMANDS_CHANNEL_ID = int(os.environ["COMMANDS_CHANNEL_ID"])
ADULT_ROLE_ID = int(os.environ["ADULT_ROLE_ID"])
MINOR_ROLE_ID = int(os.environ["MINOR_ROLE_ID"])
MAX_AGE = int(os.environ["MAX_AGE"])
MINIMUM_AGE = int(os.environ["MINIMUM_AGE"])

TOKEN = os.environ["DISCORD_API_TOKEN"]
headers = {"authorization": "Bot " + TOKEN}

def calculate_age(born: datetime):
    """Calculate the age of the user.

    :param born: the birthdate of the user
    :type born: datetime
    :return: the age of the user (in years)
    """
    today = date.today()
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    """
        if age < 0 or age > MAX_AGE:
        return None
    """
    return age

async def add_age_role(is_adult, message):
    """ Adds the appropriate age role to the user who enters their birthday into the bday-for-verification channel.

    :param is_adult: A boolean which is True if the user is at least 18 years of age and false otherwise
    :param message: The original message that was sent to the bday-for-verification channel
    """
    role_to_add = discord.utils.get(message.guild.roles, id=ADULT_ROLE_ID) if is_adult \
        else discord.utils.get(message.guild.roles, id=MINOR_ROLE_ID)
    role_to_remove = MINOR_ROLE_ID if is_adult else ADULT_ROLE_ID

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

async def enter_birthday(bot, message):
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
    if message.channel.id != BDAY_FOR_VERIFICATION_CHANNEL_ID:
        return

    logger.info(f"Message sent: {message}")

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
    bday_for_verification_channel = bot.get_channel(BDAY_FOR_VERIFICATION_CHANNEL_ID)

    if age < 0:
        logger.info(f"User {username} entered an invalid birthdate.")
        embedVar = discord.Embed(title="ERROR", description=f"Oops! You entered a birthdate that was in the "
                                                            f"future. Please enter in a valid birthdate in "
                                                            f"the {bday_for_verification_channel.name} channel."
                                 , color=0xFF5733)
        embedVar.add_field(name="Birthdate Entered", value=birth_date, inline=False)
        embedVar.set_thumbnail(url=os.environ["ERROR_ICON"])
        await bday_for_verification_channel.send("<@" + str(message.author.id) + ">")
        await bday_for_verification_channel.send(embed=embedVar)
        return
    elif age > MAX_AGE:
        logger.info(f"User {username} entered an invalid birthdate.")
        embedVar = discord.Embed(title="ERROR", description=f"Oops! You entered a birthdate that is more than **100** "
                                                            f"years in the past! By our calculations, you would be "
                                                            f"**{age} years old!** Please enter in a valid birthdate in "
                                                            f"the {bday_for_verification_channel.name} channel."
                                 , color=0xFF5733)
        embedVar.add_field(name="Birthdate Entered", value=birth_date, inline=False)
        embedVar.set_thumbnail(url=os.environ["ERROR_ICON"])
        await bday_for_verification_channel.send("<@" + str(message.author.id) + ">")
        await bday_for_verification_channel.send(embed=embedVar)
        return
    elif age < MINIMUM_AGE:
        logger.info(f"User {username} is {age} years old, too young to be in this server...")
        embedVar = discord.Embed(title="ALERT", description=f"Oops! It seems like you may be too young to be a "
                                                            f"member of {message.guild.name}. The minimum age "
                                                            f"to be in this server is **{MINIMUM_AGE}.** A server "
                                                            f"moderator may contact you shortly to resolve this "
                                                            f"issue.", color=0x9f6000)
        embedVar.set_thumbnail(url=os.environ["WARNING_ICON"])
        await bday_for_verification_channel.send("<@" + str(message.author.id) + ">")
        await bday_for_verification_channel.send(embed=embedVar)

        # Alert the server admin about the user who is too young to be in the server
        bot_alerts_channel = bot.get_channel(int(os.environ["BOT_ALERTS_CHANNEL_ID"]))
        embedVar = discord.Embed(title="ALERT", description=f"User {username} has entered in the "
                                                            f"{bday_for_verification_channel.name} channel "
                                                            f"that they are **{age} years old,** below the current "
                                                            f"minimum age of **{MINIMUM_AGE}.**", color=0x9f6000)
        embedVar.set_thumbnail(url=user_profile_picture)
        await bot_alerts_channel.send("<@" + SERVER_ADMIN_ID + ">")
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

    embedVar.add_field(name="Birthdate", value=str(birth_date), inline=False)
    embedVar.add_field(name="Age", value=str(age), inline=False)
    if is_adult:
        embedVar.add_field(name="Role", value=f"{username} has been given the role: Adult!", inline=False)
    else:
        embedVar.add_field(name="Role", value=f"{username} has been given the role: Minor!", inline=False)

    command_birth_date = birth_date_obj.strftime("%d %B")
    command_to_run = f"/override set-birthday target:@{username} date:{command_birth_date}"
    logger.info(f"The command to add {username}'s birthday to the Birthday Bot is {command_to_run}")
    embedVar.add_field(name="Command To Run", value=command_to_run, inline=False)

    # Get the commands channel object to send the messages from the bot
    commands_channel = bot.get_channel(COMMANDS_CHANNEL_ID)

    embedVar.set_thumbnail(url=user_profile_picture)
    await commands_channel.send("<@" + SERVER_ADMIN_ID + ">")
    await commands_channel.send(embed=embedVar)