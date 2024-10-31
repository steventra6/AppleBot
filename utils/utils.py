from datetime import datetime
import asyncio
import re
import aiohttp
from loguru import logger
from discord.utils import get

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

async def get_image_hash(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                # Get the filename from the URL
                filename = url.split('/')[-1]
                # Extract the hash from the filename
                hash_value = filename.split('.')[0]
                return hash_value
            else:
                return None

def image_to_bytes(image_path):
    with open(image_path, "rb") as image_file:
        return image_file.read()