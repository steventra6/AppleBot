import asyncio
import random
import discord
from discord import app_commands

from gamble import Economy

rare_items = [
    {"name": "Diamond", "value": 50},
    {"name": "Gold Ore", "value": 30},
    {"name": "Silver Ore", "value": 20},
    {"name": "Emerald", "value": 40},
    {"name": "Stevens Lucky Number", "value": 500}
]

item_data = []

class Item:
    def __init__(self, name: str, action: str, cash: int, effect: str):
        self.name = name
        self.action = action
        self.cash = cash
        self.effect = effect

    def perform_action(self, economy, user_id):
        if self.action == 'sell':
            economy.update_balance(user_id, self.cash)
            economy.remove_from_inventory(user_id, self.name)
            return f"You sold **{self.name}** for **${self.cash}**!"
        else:
            return f"The action '{self.action}' is not supported for **{self.name}**."

def create_item(name: str, action: str, cash: int, effect: str):
    item = Item(name, action, cash, effect)
    item_data.append(item)

create_item("Stevens Lucky Number", "sell", 500, "This serves no purpose.. Besides being lucky (or does it ?)")
create_item("Emerald", "sell", 400, "Can be sold for cash")
create_item("Gold Ore", "sell", 300, "Can be sold for cash")
create_item("Silver Ore", "sell", 200, "Can be sold for cash")
create_item("Fishing Rod", "increase_success_rate", 0, "Increases fishing success rate.")
create_item("Treasure Map", "find_treasure", 0, "Leads to hidden treasures.")
create_item("Old Boot", "sell", 50, "Can be used as a joke item.")
create_item("Gold Coin", "sell", 100, "Can be sold for extra cash.")
create_item("Lucky Charm", "increase_success_rate", 0, "Increases chance of rare catches.")
create_item("Diamond", "sell", 500, "Can be sold for cash")

fish_data = [
    {
        "fish": "Salmon",
        "success_message": "You caught a **Salmon**! Great job!",
        "failure_messages": [
            "You missed the fish and it splashed water in your face!",
            "The fish got away before you could reel it in!",
            "You caught a boot instead of a fish!"
        ],
        "reward": (100, 200)
    },
    {
        "fish": "Trout",
        "success_message": "You caught a **Trout**! Nice catch!",
        "failure_messages": [
            "The trout was too slippery and slipped off your hook!",
            "You ended up with seaweed instead of a fish!",
            "You scared the trout away with your noisy fishing!"
        ],
        "reward": (80, 160)
    },
    {
        "fish": "Catfish",
        "success_message": "You caught a **Catfish**! Well done!",
        "failure_messages": [
            "You tangled your line and caught nothing!",
            "You dropped your bait and the catfish laughed!",
            "You tried to catch a catfish but only caught a cold!"
        ],
        "reward": (120, 240)
    }
]



async def setup_fishing_commands(bot, economy: Economy, guild_id: str):

    @bot.tree.command(name="items", description="View your inventory items.", guild=discord.Object(id=guild_id))
    async def items(interaction: discord.Interaction):
        user_id = interaction.user.id
        inventory: Item = economy.inventories.get(user_id, [])

        embed = discord.Embed(
            title=f"{interaction.user.name}'s Inventory",
            color=discord.Color.blue()
        )

        if inventory:
            for item_name in inventory:
                item_object = next((item for item in item_data if item.name == item_name), None)
                if item_object:
                    embed.add_field(name=item_object.name, value=item_object.effect, inline=True)
        else:
            embed.add_field(name="Empty", value="You have no items in your inventory.", inline=False)

        await interaction.response.send_message(embed=embed)

    @bot.tree.command(
        name="fish",
        description="Try to catch a fish!",
        guild=discord.Object(id=guild_id)
    )
    async def fish(interaction: discord.Interaction):
        fish = random.choice(fish_data)
        await interaction.response.send_message(f"Cast your line! Try to catch a **{fish['fish']}**!")

        def check(m):
            return m.channel == interaction.channel and m.author.id == interaction.user.id

        try:
            answer_msg = await bot.wait_for('message', timeout=15.0, check=check)
        except asyncio.TimeoutError:
            await interaction.followup.send("You took too long to respond! Better luck next time!")
            return "timeout", None

        if answer_msg.content.lower() in ["yes", "y", "catch"]:
            reward = random.randint(*fish["reward"])
            economy.update_balance(interaction.user.id, reward)

            item = random.choice(item_data)
            economy.add_to_inventory(interaction.user.id, item.name)

            await interaction.followup.send(
                f"{fish['success_message']} You earned **${reward}**! You also found a **{item.name}**! ({item.effect})"
            )
            return "caught", (reward, item.name)
        else:
            fail_message = random.choice(fish["failure_messages"])
            await interaction.followup.send(f"{fail_message} Better luck next time!")
            return "failed", None

    @bot.tree.command(
        name="sell",
        description="Sell an item from your inventory.",
        guild=discord.Object(id=guild_id)
    )
    async def sell(interaction: discord.Interaction, item_name: str):
        user_id = interaction.user.id
        inventory = economy.inventories.get(user_id, [])

        item_name_lower = item_name.lower()

        inventory_lower = [item.lower() for item in inventory]

        if item_name_lower not in inventory_lower:
            await interaction.response.send_message(f"You don't have a **{item_name}** in your inventory.", ephemeral=True)
            return

        for item in item_data:
            if item.name.lower() == item_name_lower and item.action == 'sell':
                response = item.perform_action(economy, user_id)
                await interaction.response.send_message(response)
                return

        await interaction.response.send_message(f"You cannot sell **{item_name}**.", ephemeral=True)

    @bot.tree.command(name="treasure_map", description="Use a treasure map to find treasure!", guild=discord.Object(id=guild_id))
    async def treasure_map(interaction: discord.Interaction):
        user_id = interaction.user.id
        inventory = economy.inventories.get(user_id, [])
        
        if "Treasure Map" not in inventory:
            await interaction.response.send_message("You don't have a treasure map to use!")
            return
        
        economy.remove_from_inventory(user_id, "Treasure Map")

        coins_found = random.randint(20, 100)
        rare_item_chance = random.random()
        rare_item = None
        
        if rare_item_chance < 0.5:
            rare_item = random.choice(rare_items)
            economy.add_to_inventory(user_id, rare_item["name"])
        
        economy.update_balance(user_id, coins_found)
        
        response_message = f"You found **${coins_found}**!"
        
        if rare_item:
            response_message += f" You also found a **{rare_item['name']}**!"
        
        await interaction.response.send_message(response_message)
