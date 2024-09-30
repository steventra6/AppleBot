
# **APPLE BOT!** 🍎



![KID APPLE! x Discord](./docs/images/kid%20apple%20github%20logo.png)


## Introduction 📝

**Apple Bot** is a simple, whimsical Discord Bot written specifically for the **KID APPLE!** Discord Server.

*KID APPLE!* is a gaming-based [Discord Server](https://discord.com/) where friends can chill, hang out, play video games, watch movies, and have fun! It is a community of like-minded people, and we strive to create an environment that's fun for everyone! *KID APPLE!* is run by me, [Steven Tra](https://github.com/steventra6), otherwise known to users on Discord as kidaspire. 

## Remembering Birthdays 🎂

The minimum age to join the server is currently **16.** We have a text channel for verification named "bday-for-verification" where users can input their birthdates in a *MM/DD/YYYY* format. A server admin/moderator will give them the role of "Minor" (if they are under the age of 18) or "18+" (if they are at least 18). Also, the server admin/mod will input their birthday into a third-party [Birthday Bot](https://noithecat.dev/bots/BirthdayBot/) which alerts members of the server when people's birthdays are coming up.

As a server admin, it was *incredibly tedious* to manually assign people roles and enter in birthdays, so I wrote Apple Bot to automate that process! I will describe how it works below.

### How it works:
- Users will enter their birthdate (MM/DD/YYYY) in the "bday-for-verification" channel.
- Apple Bot parses their birthdate, does some error checking, assigns them the role of Minor or 18+, and then constructs the exact command to input their birthday in the Birthday Bot. Apple Bot sends a message over to the private "commands" text channel *(only viewable by admins/moderators)* so that an admin/mod can enter in the command to set their birthday. 

Originally, I wanted Apple Bot to automatically enter user birthdays into Birthday Bot directly, but I learned that this isn't possible or ethical due to Discord's Terms of Service. Therefore, I settled on the next best thing which is formatting the command beforehand, so all a server admin/moderator has to do is copy and paste the command. 

## Reminding Users About Server Events 🎉

One thing we love to do in KID APPLE! is have server-wide events (usually on the weekends). Usually, I like to send reminders about the events 60 to 30 minutes before they start, and as I was developing Apple Bot, I felt that this would be a good opportunity to automate that process as well. Therefore, I included a feature in Apple Bot that sends out reminder messages about an event to a designated "updates" channel. 

### How it works:
- A server/admin moderator will create an event in Discord
- Apple Bot will extract the details of the event and post an announcement about it to the updates channel
- As the event approaches, the bot will send out reminder messages to the updates channel in intervals that the repo owner (that's you!) specifies. As of right now, you may only specifies intervals in minutes *(e.g. 60 minutes before the event, 30 minutes before the event, etc.)*, but future versions might allow more flexibility.  

Although it's a small feature, it helps tremendously in reminding everyone when events are happening (myself included), especially as the server grows large in numbers. 



## Installation ⛭

- [Create your own Discord Bot and retrieve a Discord API token](https://discordpy.readthedocs.io/en/stable/discord.html)

- To build **Apple Bot,** you need Python 3.11+. The latest version of Python can be downloaded [here](https://www.python.org/downloads/).  

- You also need to install [Poetry](https://python-poetry.org/) to handle dependency management across libraries. Instructions on how to download and install Poetry can be found [here](https://python-poetry.org/docs/#installing-with-pipx). 

- Once Poetry is installed, run `poetry install` in the root directory of this project. This will download and resolve all dependencies for this project. 

- Create a `.env` file in the root directory of this project if running locally. *(Note: if you are running this project on the Cloud or a CI/CD pipeline, you may skip the following step. Please use their method of setting environment variables.)* 

    
## Environment Variables 🌎

In your `.env` file, enter in the values for your Discord API token, server admin ID (i.e. the numeric User ID of the admin responsible for entering commands), channel IDs, minor/adult role IDs, minimum age, and reminder times. Your `.env` file should look like this after you have finished *(with actual values subsituted instead of the dummy values shown below).*

```bash
DISCORD_API_TOKEN=<"your_discord_api_token">
TIMEZONE="UTC"
DISCORD_SERVER_ADMIN_ID=<"your_server_admin_id">
BDAY_FOR_VERIFICATION_CHANNEL_ID=<your_bday_for_verification_channel_id>
COMMANDS_CHANNEL_ID=<your_commands_channel_id>
BOT_ALERTS_CHANNEL_ID=<your_bot_alerts_channel_id>
UPDATES_CHANNEL_ID=<your_updates_channel_id>
MINOR_ROLE_ID=<your_minor_role_id>
ADULT_ROLE_ID=<your_adult_role_id>
MINIMUM_AGE=<your_servers_minimum_age>
REMINDER_TIMES="[30, 15, 10, 5, 1, 0]" # These numbers can be changed to whatever you want
```


## Run Locally 🏃

Use Poetry to start the bot

```bash
  poetry run python main.py
```

If everything is working, you should see the text `Apple Bot is ready!` logged to the console. 

**Now you are officially ready to start using Apple Bot. Enjoy! 😋**

## Logging ✍️

Apple Bot uses [Loguru](https://github.com/Delgan/loguru) to log all system output. The logs are found in `./logs` by default. Logs are created daily, but this can be changed in the logging configuration.
## Authors 📖

- [Steven Tra (@steventra6)](https://github.com/steventra6)


## Feedback 🗣️

If you have any questions, concerns, or general feedback, please feel free to reach out to me on LinkedIn or by email at steven.tra6@gmail.com! 


## License 📚

[MIT](https://choosealicense.com/licenses/mit/)

