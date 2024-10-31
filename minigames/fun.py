import asyncio
from datetime import timedelta
import math
import random
from typing import Dict, List
import discord
from discord import ButtonStyle, app_commands
from loguru import logger

from minigames.gamble import Economy


rare_items = [
    {"name": "Diamond", "value": 300},
    {"name": "Gold Ore", "value": 75},
    {"name": "Silver Ore", "value": 145},
    {"name": "Emerald", "value": 200},
    {"name": "Stevens Lucky Number", "value": 500}
]

item_data = []

class Item:
    def __init__(self, name: str, action: str, cash: int, effect: str):
        self.name = name
        self.action = action
        self.cash = cash
        self.effect = effect

    def perform_action(self, economy, user: discord.Interaction.user):
        if self.action == 'sell':
            economy.update_balance(user.id, self.cash)
            economy.remove_from_inventory(user.id, self.name)
            logger.debug(f"{user.name} sold {self.name} for {self.cash}!")
            return f"You sold **{self.name}** for **${self.cash}**!"
        else:
            logger.debug(f"{user.name} tried to use the action {self.action} which is not supported for {self.name}")
            return f"The action '{self.action}' is not supported for **{self.name}**."

def create_item(name: str, action: str, cash: int, effect: str):
    item = Item(name, action, cash, effect)
    item_data.append(item)

create_item("Stevens Lucky Number", "sell", 500, "This serves no purpose.. Besides being lucky (or does it ?)")
create_item("Emerald", "sell", 200, "Can be sold for cash")
create_item("Gold Ore", "sell", 75, "Can be sold for cash")
create_item("Silver Ore", "sell", 145, "Can be sold for cash")
create_item("Fishing Rod", "increase_success_rate", 0, "Increases fishing success rate.")
create_item("Treasure Map", "find_treasure", 0, "Leads to hidden treasures.")
create_item("Old Boot", "sell", 50, "Can be used as a joke item.")
create_item("Gold Coin", "sell", 100, "Can be sold for extra cash.")
create_item("Lucky Charm", "increase_success_rate", 0, "Increases chance of rare catches.")
create_item("Diamond", "sell", 300, "Can be sold for cash")

fish_data = [
    {
        "fish": "Salmon",
        "success_message": "You caught a **Salmon**! Great job!",
        "failure_messages": [
            "You missed the fish and it splashed water in your face!",
            "The fish got away before you could reel it in!",
            "You caught a boot instead of a fish!"
        ],
        "reward": (10, 100)
    },
    {
        "fish": "Trout",
        "success_message": "You caught a **Trout**! Nice catch!",
        "failure_messages": [
            "The trout was too slippery and slipped off your hook!",
            "You ended up with seaweed instead of a fish!",
            "You scared the trout away with your noisy fishing!"
        ],
        "reward": (40, 100)
    },
    {
        "fish": "Catfish",
        "success_message": "You caught a **Catfish**! Well done!",
        "failure_messages": [
            "You tangled your line and caught nothing!",
            "You dropped your bait and the catfish laughed!",
            "You tried to catch a catfish but only caught a cold!"
        ],
        "reward": (65, 100)
    }
]


class InventoryPaginationView(discord.ui.View):
    def __init__(self, items: List[tuple], user_name: str, items_per_page: int = 5):
        super().__init__(timeout=60)
        self.items = items
        self.current_page = 0
        self.items_per_page = items_per_page
        self.user_name = user_name
        self.total_pages = math.ceil(len(items) / items_per_page)
        
        if self.total_pages <= 1:
            self.previous_button.disabled = True
            self.next_button.disabled = True

    def get_embed(self) -> discord.Embed:
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        current_items = self.items[start_idx:end_idx]

        embed = discord.Embed(
            title=f"{self.user_name}'s Inventory",
            description=f"Page {self.current_page + 1} of {self.total_pages}",
            color=discord.Color.blue()
        )

        if current_items:
            for item_name, quantity, effect in current_items:
                embed.add_field(
                    name=f"{item_name} (x{quantity})",
                    value=f"📝 {effect}",
                    inline=False
                )
        else:
            embed.add_field(
                name="Empty",
                value="You have no items in your inventory.",
                inline=False
            )

        return embed

    @discord.ui.button(label="Previous", style=ButtonStyle.primary, emoji="⬅️")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Next", style=ButtonStyle.primary, emoji="➡️")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            await interaction.response.defer()

async def setup_fishing_commands(bot, economy: Economy, guild_id: str):

    @bot.tree.command(name="items", description="View your inventory items.", guild=discord.Object(id=guild_id))
    async def items(interaction: discord.Interaction):
        user_id = interaction.user.id
        inventory: Dict[str, int] = {}
        
        for item_name in economy.inventories.get(user_id, []):
            inventory[item_name] = inventory.get(item_name, 0) + 1
        
        inventory_items = []
        for item_name, quantity in inventory.items():
            item_object = next((item for item in item_data if item.name == item_name), None)
            if item_object:
                inventory_items.append((item_object.name, quantity, item_object.effect))
        
        inventory_items.sort(key=lambda x: x[0])
        
        view = InventoryPaginationView(inventory_items, interaction.user.name)
        await interaction.response.send_message(embed=view.get_embed(), view=view)

    @bot.tree.command(
        name="fish",
        description="Try to catch a fish!",
        guild=discord.Object(id=guild_id)
    )
    async def fish(interaction: discord.Interaction):
        fish = random.choice(fish_data)
        user_id = interaction.user.id
        cooldown_duration = timedelta(seconds=10)

        if economy.is_on_cooldown(user_id, 'fish'):
            remaining_time = economy.get_cooldown_time(user_id, 'fish')
            strignCause = f"{remaining_time.total_seconds()}"
            logger.debug(f"{interaction.user.name} is on cooldown for fishing. They must wait {strignCause.split('.')[0]} seconds...")
            await interaction.response.send_message(
                f"⏳ You are on cooldown! Please wait {strignCause.split('.')[0]}.", ephemeral=True
            )
            return

        logger.debug(f"{interaction.user.name} is trying to catch a fish!")
        await interaction.response.send_message(f"Cast your line! Try to catch a **{fish['fish']}**! (say y, yes or catch)")

        def check(m):
            return m.channel == interaction.channel and m.author.id == interaction.user.id

        try:
            answer_msg = await bot.wait_for('message', timeout=15.0, check=check)
        except asyncio.TimeoutError:
            logger.debug(f"{interaction.user.name} took too long to respond to catch the fish...")
            await interaction.followup.send("You took too long to respond! Better luck next time!")
            return "timeout", None

        if answer_msg.content.lower() in ["yes", "y", "catch"]:
            reward = random.randint(*fish["reward"])
            economy.update_balance(interaction.user.id, reward)

            rare_item_chance = random.random()
            found_item = None

            if rare_item_chance < 0.10:
                found_item = random.choice(rare_items)
                economy.add_to_inventory(interaction.user.id, found_item["name"])

            # too commoon # 
            # common_item = random.choice(item_data)
            # economy.add_to_inventory(interaction.user.id, common_item.name)

            logger.debug(f"{interaction.user.name} earned {reward}!")
            response_message = f"{fish['success_message']} You earned **${reward}**!"
            
            if found_item:
                logger.debug(f"{interaction.user.name} also found a {found_item['name']}!")
                response_message += f" You also found a **{found_item['name']}**! ({found_item['value']} value)"
            
            # response_message += f" You also found a **{common_item.name}**! ({common_item.effect})"
            
            economy.set_cooldown(interaction.user.id, "fish", cooldown_duration)

            await interaction.followup.send(response_message)
            return "caught", (reward)

        else:
            cooldown_duration = timedelta(seconds=10)
            economy.set_cooldown(interaction.user.id, "fish", cooldown_duration)

            fail_message = random.choice(fish["failure_messages"])
            logger.debug(f"{interaction.user.name} failed at fishing...")
            await interaction.followup.send(f"{fail_message} Better luck next time!")
            return "failed", None
            

    @bot.tree.command(
        name="sell",
        description="Sell an item from your inventory.",
        guild=discord.Object(id=guild_id)
    )
    async def sell(interaction: discord.Interaction, item_name: str):
        user = interaction.user
        #user_id = interaction.user.id
        inventory = economy.inventories.get(user.id, [])

        item_name_lower = item_name.lower()

        inventory_lower = [item.lower() for item in inventory]

        if item_name_lower not in inventory_lower:
            logger.error(f"{interaction.user.name} tried to sell {item_name}, but they don't have it in their inventory!")
            await interaction.response.send_message(f"You don't have a **{item_name}** in your inventory.", ephemeral=True)
            return

        for item in item_data:
            if item.name.lower() == item_name_lower and item.action == 'sell':
                response = item.perform_action(economy, user)
                await interaction.response.send_message(response)
                return

        logger.error(f"{interaction.user.name} cannot sell {item_name}")
        await interaction.response.send_message(f"You cannot sell **{item_name}**.", ephemeral=True)

    @bot.tree.command(name="treasure_map", description="Use a treasure map to find treasure!", guild=discord.Object(id=guild_id))
    async def treasure_map(interaction: discord.Interaction):
        user_id = interaction.user.id
        inventory = economy.inventories.get(user_id, [])
        
        if "Treasure Map" not in inventory:
            logger.error(f"{interaction.user.name} tried to use a treasure map, but they don't have one in their inventory!")
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

        logger.debug(f"{interaction.user.name} found {coins_found}")
        response_message = f"You found **${coins_found}**!"
        
        if rare_item:
            logger.debug(f"{interaction.user.name} found a {rare_item['name']}")
            response_message += f" You also found a **{rare_item['name']}**!"
        
        await interaction.response.send_message(response_message)
