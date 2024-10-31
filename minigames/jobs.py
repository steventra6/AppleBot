import os
import asyncio
from datetime import timedelta
import discord
from discord import app_commands
import random
import minigames.gamble as gamble
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

jobs = {
    "Baker": (100, 200),
    "Farmer": (80, 160),
    "Carpenter": (90, 180),
    "Miner": (70, 140),
    "Engineer": (120, 240),
    "Chef": (140, 280),
    "Hunter": (100, 200),
    "Blacksmith": (120, 220),
    "Merchant": (90, 180),
    "Wizard": (160, 320)
}

task_data = {
    "Baker": [
        {
            "question": "What's the main ingredient needed to make bread rise?",
            "answers": ["yeast", "active yeast", "fresh yeast", "dry yeast"]
        },
        {
            "question": "What ingredient makes pastries flaky?",
            "answers": ["butter", "margarine", "fat", "shortening"]
        },
        {
            "question": "What do you need to prevent dough from sticking?",
            "answers": ["flour", "cornstarch", "powder"]
        },
        {
            "question": "What tool do bakers use to measure ingredients precisely?",
            "answers": ["scale", "weights", "measuring cups", "cups", "spoons"]
        }
    ],
    "Farmer": [
        {
            "question": "What do you need to prepare soil for planting?",
            "answers": ["plow", "tractor", "hoe", "tiller", "spade"]
        },
        {
            "question": "What helps plants grow better?",
            "answers": ["fertilizer", "compost", "manure", "nutrients"]
        },
        {
            "question": "What do you use to keep pests away from crops?",
            "answers": ["pesticide", "insecticide", "scarecrow", "netting"]
        },
        {
            "question": "What's essential for crops to survive?",
            "answers": ["water", "irrigation", "rain", "moisture"]
        }
    ],
    "Carpenter": [
        {
            "question": "What tool do you use to join pieces of wood together?",
            "answers": ["hammer", "nail gun", "screwdriver", "drill"]
        },
        {
            "question": "What do you use to measure wood accurately?",
            "answers": ["tape measure", "ruler", "measuring tape", "square"]
        },
        {
            "question": "What tool makes straight cuts in wood?",
            "answers": ["saw", "handsaw", "circular saw", "table saw"]
        },
        {
            "question": "What keeps wooden joints together?",
            "answers": ["nails", "screws", "glue", "wood glue", "dowels"]
        }
    ],
    "Miner": [
        {
            "question": "What tool breaks through rock?",
            "answers": ["pickaxe", "drill", "jackhammer", "hammer"]
        },
        {
            "question": "What precious metal is commonly mined?",
            "answers": ["gold", "silver", "copper", "iron"]
        },
        {
            "question": "What do miners use to see underground?",
            "answers": ["lamp", "torch", "headlamp", "light"]
        },
        {
            "question": "What safety equipment do miners need?",
            "answers": ["helmet", "hard hat", "mask", "goggles"]
        }
    ],
    "Engineer": [
        {
            "question": "What do you use to plan a structure?",
            "answers": ["blueprint", "drawing", "plan", "sketch", "design"]
        },
        {
            "question": "What calculation tool is essential for engineers?",
            "answers": ["calculator", "computer", "software", "cad"]
        },
        {
            "question": "What science is crucial for engineering?",
            "answers": ["physics", "math", "mathematics", "mechanics"]
        },
        {
            "question": "What do you use to measure precise angles?",
            "answers": ["protractor", "compass", "square", "angle finder"]
        }
    ],
    "Chef": [
        {
            "question": "What's used to measure cooking temperature?",
            "answers": ["thermometer", "probe", "timer"]
        },
        {
            "question": "What tool is used for mixing ingredients?",
            "answers": ["whisk", "mixer", "spoon", "blender"]
        },
        {
            "question": "What's essential for sautéing food?",
            "answers": ["pan", "oil", "butter", "skillet"]
        },
        {
            "question": "What tool is used to chop ingredients?",
            "answers": ["knife", "cleaver", "chopper", "blade"]
        }
    ],
    "Hunter": [
        {
            "question": "What weapon is used for long-range hunting?",
            "answers": ["bow", "crossbow", "rifle", "gun"]
        },
        {
            "question": "What do hunters use to track animals?",
            "answers": ["tracks", "footprints", "compass", "map"]
        },
        {
            "question": "What catches small game?",
            "answers": ["trap", "snare", "net", "cage"]
        },
        {
            "question": "What do hunters wear to blend in?",
            "answers": ["camouflage", "camo", "ghillie suit", "camouflage suit"]
        }
    ],
    "Blacksmith": [
        {
            "question": "What tool shapes hot metal?",
            "answers": ["hammer", "anvil", "tongs", "mallet"]
        },
        {
            "question": "What heats the metal for forging?",
            "answers": ["forge", "furnace", "fire", "kiln"]
        },
        {
            "question": "What metal is commonly forged?",
            "answers": ["iron", "steel", "bronze", "metal"]
        },
        {
            "question": "What cools hot metal quickly?",
            "answers": ["water", "oil", "quench", "bucket"]
        }
    ],
    "Merchant": [
        {
            "question": "What's used to store money?",
            "answers": ["coins", "gold", "cash", "wallet", "purse"]
        },
        {
            "question": "What's used to track sales?",
            "answers": ["ledger", "book", "register", "records"]
        },
        {
            "question": "How do merchants advertise their goods?",
            "answers": ["signs", "posters", "flyers", "advertisements"]
        },
        {
            "question": "What's needed for fair trade?",
            "answers": ["scale", "weights", "measure", "balance"]
        }
    ],
    "Wizard": [
        {
            "question": "What channels magical power?",
            "answers": ["wand", "staff", "rod", "crystal"]
        },
        {
            "question": "What contains magical brews?",
            "answers": ["potion", "bottle", "vial", "flask"]
        },
        {
            "question": "What's used to cast spells?",
            "answers": ["magic", "mana", "energy", "power"]
        },
        {
            "question": "What records magical knowledge?",
            "answers": ["spellbook", "grimoire", "tome", "scroll", "scrolls"]
        }
    ]
}

failure_messages = {
    "Baker": [
        "You tried to bake, but instead, you created a volcano of flour.",
        "Your culinary skills just took a nosedive; the kitchen is now a smoke-filled disaster zone.",
        "Your attempt at making bread resulted in a brick-hard creation.",
        "The cookies you baked could be used as doorstops.",
        "Your cake collapsed faster than your baking dreams.",
        "Even the local pigeons refused your bread."
    ],
    "Farmer": [
        "You planted seeds, but all you grew was a field of weeds.",
        "Your harvest was so bad, even the crows left in disappointment.",
        "You tried to milk a cow, but it turns out, it was just a very grumpy goat.",
        "Your crops grew sideways instead of upwards.",
        "The scarecrow you built scared away other farmers instead.",
        "Your vegetables came out square-shaped somehow."
    ],
    "Carpenter": [
        "You built a chair that could only be used as firewood.",
        "Your attempt at furniture design resulted in a modern art piece no one understands.",
        "You measured twice and cut once... but it was the wrong piece entirely.",
        "Your table has five legs, and it still wobbles.",
        "The birdhouse you built is now a squirrel fortress.",
        "Your wooden horse looks more like a giraffe with arthritis."
    ],
    "Miner": [
        "You went mining but returned with nothing but dirt and disappointment.",
        "You struck something, but it was just a rock—no gold in sight.",
        "Your mining skills are legendary... for their complete ineptitude.",
        "You dug straight down and found bedrock... and shame.",
        "Your pickaxe broke on the first swing.",
        "You found fool's gold and were fooled by it."
    ],
    "Engineer": [
        "You built a bridge that only leads to confusion.",
        "Your invention is so advanced that it defies the laws of physics—and logic.",
        "You aimed to innovate, but you ended up with a pile of scrap metal.",
        "Your robot assistant became self-aware and quit.",
        "Your perpetual motion machine stopped permanently.",
        "Your blueprint looks like a child's crayon drawing."
    ],
    "Chef": [
        "Your soufflé collapsed, turning it into a pancake.",
        "You tried to flambé, but instead, you nearly burnt down the kitchen.",
        "Your dish looked great but tasted like cardboard.",
        "The health inspector took one look and ran away.",
        "Your signature dish made everyone sign away their appetite.",
        "Even the garbage disposal rejected your cooking."
    ],
    "Hunter": [
        "You went hunting but only managed to scare off the game.",
        "Your aim was so bad that even the rabbits laughed.",
        "You set traps but caught nothing but your own shoelaces.",
        "You followed tracks that led back to your own camp.",
        "The deer took selfies with you while you weren't looking.",
        "Your hunting call attracted a group of confused tourists."
    ],
    "Blacksmith": [
        "You forged a sword that was as useful as a wet noodle.",
        "Your hammer skills produced more noise than results.",
        "You melted down the wrong metal, creating a blob of uselessness.",
        "Your anvil has dents from missing the metal entirely.",
        "The armor you made has more holes than Swiss cheese.",
        "Your throwing axe refused to be thrown."
    ],
    "Merchant": [
        "You tried to sell your wares, but no one was interested.",
        "Your bargaining skills left you with empty pockets.",
        "You promised a good deal, but it turned out to be a total rip-off.",
        "Your shop attracted exactly zero customers today.",
        "You bought high and sold low... again.",
        "Your marketing campaign attracted pigeons instead of customers."
    ],
    "Wizard": [
        "You attempted a spell, but instead, you turned your hair into spaghetti.",
        "Your potion exploded, creating a colorful mess.",
        "You conjured a creature, but it was a very angry cat.",
        "Your magic wand started telling dad jokes.",
        "Your levitation spell worked... on your shoes only.",
        "Your transformation spell turned you into a disappointed parent."
    ]
}

async def complete_job_task(bot, interaction: discord.Interaction, job_name: str):
    task = random.choice(task_data[job_name])
    
    steal_messages = [
        "swooped in like a sneaky raccoon and stole half the money!",
        "pulled off the perfect heist while you weren't looking!",
        "channeled their inner ninja and made off with some cash!",
        "did a classic 'look over there!' trick and grabbed the money!",
        "used their pickpocket skills from playing too many RPGs!",
        "distracted you with a rubber duck while taking the cash!",
        "borrowed your money 'indefinitely' without asking!",
        "performed a magic trick - your money disappeared!",
        "pulled a fast one while you were thinking about the answer!",
        "learned from their years of playing Monopoly and took their chance!",
        "used the classic 'is that your wallet floating away?' distraction!",
        "studied the art of money liberation from Robin Hood!",
        "practiced their stealth skills from watching too many heist movies!",
        "remembered their training from the School of Sneaky Snacks!",
        "mastered the art of the quick-grab from their cat!"
    ]
    
    failed_steal_messages = [
        "tried to steal but tripped over their own feet and dropped their wallet!",
        "attempted a heist but forgot to wear their lucky stealing socks!",
        "failed their Stealth check and lost some gold!",
        "should probably stick to their day job instead of stealing!",
        "forgot that stealing is harder than it looks in the movies!",
        "learned that crime doesn't pay... literally lost money!",
        "discovered they're not cut out for a life of crime!",
        "successfully failed at becoming a master thief!",
        "might need more practice at this whole stealing thing!",
        "donated to your cause involuntarily!"
    ]
    
    await interaction.response.send_message(f"To complete your job as a **{job_name}**, answer this question: `{task['question']}`")

    def check(m):
        return m.channel == interaction.channel

    try:
        answer_msg = await bot.wait_for('message', timeout=15.0, check=check)
    except asyncio.TimeoutError:
        logger.debug(f"{interaction.user.name} took too long to respond to their {job_name} question...")
        await interaction.followup.send("You took too long to respond!")
        return ("timeout", None, None)

    is_correct = answer_msg.content.lower() in [ans.lower() for ans in task['answers']]

    if answer_msg.author.id == int(os.environ["APPLE_BOT_ID"]):
        logger.debug(f"{interaction.user.name} ran /work twice without responding to the first /work command.")
        await interaction.followup.send(f"You must answer your **{job_name}** question before running /work again!")
        return ("timeout", None, None)
    if answer_msg.author.id != interaction.user.id and answer_msg.author.id != int(os.environ["APPLE_BOT_ID"]):
        if is_correct:
            steal_message = random.choice(steal_messages)
            logger.debug(f"{answer_msg.author.name} stole from {interaction.user.name}")
            await answer_msg.reply(f"Oh no! **{answer_msg.author.name}** {steal_message}")
            return ("stolen", answer_msg.author.id, None)
        else:
            fail_message = random.choice(failed_steal_messages)
            logger.debug(f"{answer_msg.author.name} failed to steal from {interaction.user.name}")
            await answer_msg.reply(f"**{answer_msg.author.name}** {fail_message}")
            return ("failed_steal", answer_msg.author.id, task)
    else:
        return ("completed" if is_correct else "failed", None, None)
async def setup_job_system(bot, economy: gamble.Economy, guild_id: str):

    @bot.tree.command(
        name="work",
        description="Select a job to earn money!",
        guild=discord.Object(id=guild_id)
    )
    @app_commands.describe(job="The job you want to perform")
    @app_commands.choices(
        job=[app_commands.Choice(name=job, value=job) for job in jobs.keys()]
    )
    async def work(interaction: discord.Interaction, job: app_commands.Choice[str]):
        user_id = interaction.user.id
        job_name = job.value
        min_reward, max_reward = jobs[job_name]
        performance = random.randint(1, 100)
        cooldown_duration = timedelta(seconds=10)

        if economy.is_on_cooldown(user_id, 'work'):
            remaining_time = economy.get_cooldown_time(user_id, 'work')
            strignCause = f"{remaining_time.total_seconds()}"
            logger.debug(f"{interaction.user.name} is on cooldown for using the /work command. They must wait {strignCause.split('.')[0]} seconds")
            await interaction.response.send_message(
                f"⏳ You are on cooldown! Please wait {strignCause.split('.')[0]}.", ephemeral=True
            )
            return

        task_result = await complete_job_task(bot, interaction, job_name)
        
        if isinstance(task_result, tuple):
            status, stealer_id, task = task_result
        else:
            status, stealer_id, task = "failed", None, None

        embed = discord.Embed()
        
        if status == "failed":
            reward = random.randint(min_reward // 4, min_reward // 2)
            logger.debug(f"{interaction.user.name} failed at {job_name}. They earned ${reward} for trying.")
            embed.description = f"That wasn't quite right... {random.choice(failure_messages[job_name])}\nYou still earned **${reward}** for trying!"
            embed.color = discord.Color.red()
            
        elif status == "failed_steal":
            penalty = random.randint(min_reward // 2, min_reward)
            economy.update_balance(stealer_id, -penalty)
            
            def check(m):
                return m.author.id == interaction.user.id and m.channel == interaction.channel
                
            try:
                answer_msg = await bot.wait_for('message', timeout=15.0, check=check)
                if answer_msg.content.lower() in [ans.lower() for ans in task['answers']]:
                    reward = random.randint(max_reward * 2, int(max_reward * 2.5))
                    await answer_msg.reply(f"You worked as a **{job_name}** and got double pay for catching the thief! You earned **${reward}**!")
                else:
                    reward = random.randint(min_reward // 4, min_reward // 2)
                    await answer_msg.reply(f"You worked as a **{job_name}** but couldn't get it right. You earned **${reward}**.")
            except asyncio.TimeoutError:
                reward = random.randint(min_reward // 4, min_reward // 2)
                await interaction.followup.send(f"You worked as a **{job_name}** but took too long to answer. You earned **${reward}**.")

            logger.debug(f"{interaction.user.name} worked as a {job_name} and earned ${reward}")

            economy.update_balance(user_id, reward)
            return
            
        elif status == "stolen":
            original_reward = random.randint(min_reward, max_reward)
            stolen_amount = original_reward // 2
            
            economy.update_balance(user_id, original_reward - stolen_amount)
            economy.update_balance(stealer_id, stolen_amount)
            reward = original_reward - stolen_amount
            embed.description = f"You worked as a **{job_name}** and earned **${reward}**."
            embed.color = discord.Color.blue()
            
        elif status == "completed":
            if performance >= 80:
                reward = random.randint(max_reward, int(max_reward * 1.5))
                logger.debug(f"{interaction.user.name} worked as a {job_name} and earned ${reward}")
                embed.description = f"Correct! You worked as a **{job_name}** and did an excellent job! You earned **${reward}**!"
                embed.color = discord.Color.green()
            else:
                reward = random.randint(min_reward, max_reward)
                logger.debug(f"{interaction.user.name} worked as a {job_name} and earned ${reward}")
                embed.description = f"Correct! You worked as a **{job_name}** and earned **${reward}**."
                embed.color = discord.Color.blue()

        if status not in ["stolen", "failed_steal", "timeout"]:
            economy.update_balance(user_id, reward)
            
        if status != "timeout":
            await interaction.followup.send(embed=embed)

        economy.set_cooldown(interaction.user.id, 'work', cooldown_duration)