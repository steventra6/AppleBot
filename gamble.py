from datetime import datetime, timedelta
import os
from typing import Dict
import discord
import random
from discord.ext import commands
import json

class Economy:
    def __init__(self, save_file: str = "economy.json"):
        self.save_file = save_file
        self.balances: Dict[int, int] = {}
        self.cooldowns: Dict[int, Dict[str, Dict[str, any]]] = {}
        
        os.makedirs(os.path.dirname(save_file), exist_ok=True)
        self.load_data()

    def load_data(self):
        """Load balance and cooldown data from JSON file"""
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r') as f:
                    data = json.load(f)
                    self.balances = {int(k): v for k, v in data["balances"].items()}
                    self.cooldowns = {int(k): v for k, v in data.get("cooldowns", {}).items()}
            else:
                self.balances = {}
                self.cooldowns = {}
        except Exception as e:
            print(f"Error loading economy data: {e}")
            self.balances = {}
            self.cooldowns = {}

    def save_data(self):
        """Save balance and cooldown data to JSON file"""
        try:
            data = {
                "balances": self.balances,
                "cooldowns": self.cooldowns
            }
            with open(self.save_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving economy data: {e}")

    def get_balance(self, user_id: int) -> int:
        return self.balances.get(user_id, 1000)
    
    def update_balance(self, user_id: int, amount: int) -> int:
        current_balance = self.get_balance(user_id)
        self.balances[user_id] = current_balance + amount
        self.save_data()
        return self.balances[user_id]

    def set_cooldown(self, user_id: int, command: str, cooldown_duration: timedelta):
        cooldown_time = datetime.now() + cooldown_duration
        if user_id not in self.cooldowns:
            self.cooldowns[user_id] = {}
        self.cooldowns[user_id][command] = {
            "cooldown": cooldown_time.isoformat()
        }
        self.save_data()

    def is_on_cooldown(self, user_id: int, command: str) -> bool:
        if user_id not in self.cooldowns or command not in self.cooldowns[user_id]:
            return False
        cooldown_str = self.cooldowns[user_id][command]["cooldown"]
        cooldown = datetime.fromisoformat(cooldown_str)
        return datetime.now() < cooldown

    def get_cooldown_time(self, user_id: int, command: str) -> timedelta:
        """Returns remaining cooldown time as a timedelta"""
        if user_id not in self.cooldowns or command not in self.cooldowns[user_id]:
            return timedelta(0)
        cooldown_str = self.cooldowns[user_id][command]["cooldown"]
        cooldown = datetime.fromisoformat(cooldown_str)
        return max(timedelta(0), cooldown - datetime.now())



async def setup_economy_commands(bot, economy: Economy, guild_id: str):

    @bot.tree.command(
        name="gamble",
        description="gamble your coins! Use /gamble <amount>",
        guild=discord.Object(id=guild_id)
    )
    async def gam(interaction: discord.Interaction, amount: int):
        user_id = interaction.user.id
        command_name = "gamble"
        cooldown_duration = timedelta(seconds=2)
        if economy.is_on_cooldown(user_id, command_name):
            remaining_time = economy.get_cooldown_time(user_id, command_name)
            strignCause = f"{remaining_time.total_seconds()}"
            await interaction.response.send_message(
                f"⏳ You are on cooldown! Please wait {strignCause.split('.')[0]}.", ephemeral=True
            )
            return
        
        current_balance = economy.get_balance(user_id)
        
        if amount <= 0:
            await interaction.response.send_message("You must gamble at least 1 coin!", ephemeral=True)
            return
        
        if amount > current_balance:
            await interaction.response.send_message(f"You don't have enough coins! Your balance: {current_balance}", ephemeral=True)
            return

        roll = random.randint(1, 100)
        
        if roll <= 45:  # 45% -> lose all
            economy.update_balance(user_id, -amount)
            result = f"💸 You lost {amount} coins! New balance: {economy.get_balance(user_id)}"
        elif roll <= 80:  # 35% -> 1.5x
            winnings = int(amount * 1.5)
            economy.update_balance(user_id, winnings - amount)
            result = f"🎉 You won {winnings} coins! New balance: {economy.get_balance(user_id)}"
        elif roll <= 95:  # 15% -> 2x
            winnings = amount * 2
            economy.update_balance(user_id, winnings - amount)
            result = f"🎊 Double win! You won {winnings} coins! New balance: {economy.get_balance(user_id)}"
        elif roll <= 99:  # 5% -> 3x
            winnings = amount * 3
            economy.update_balance(user_id, winnings + amount)
            result = f"🌟 JACKPOT! Triple win! You won {winnings} coins! New balance: {economy.get_balance(user_id)}"
        else: 
            winnings = amount * 10
            economy.update_balance(user_id, winnings + amount)
            result = f"🌟 LUCKY ME CHARMS! 10x win! You won {winnings} coins! New balance: {economy.get_balance(user_id)}"
        
        embed = discord.Embed(
            title="🎰 Gambling Results",
            description=result,
            color=discord.Color.gold() if roll > 45 else discord.Color.red()
        )
        embed.set_footer(text=f"Roll: {roll}/100")

        economy.set_cooldown(user_id, command_name, cooldown_duration)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(
        name="balance",
        description="Check your current balance",
        guild=discord.Object(id=guild_id)
    )
    async def balance(interaction: discord.Interaction):
        user_id = interaction.user.id
        current_balance = economy.get_balance(user_id)
        
        embed = discord.Embed(
            title="💰 Balance",
            description=f"Your current balance: {current_balance} coins",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(
        name="set",
        description="Set your balance to a specific amount",
        guild=discord.Object(id=guild_id)
    )
    async def setBalance(interaction: discord.Interaction, amount: int):
        user_id = interaction.user.id
        
        if amount < 0:
            await interaction.response.send_message("Amount cannot be negative!", ephemeral=False)
            return
            
        new_balance = economy.update_balance(user_id, amount)
        
        embed = discord.Embed(
            title="💰 Balance Updated",
            description=f"Your balance has been set to: {new_balance} coins",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(
        name="steal",
        description="Attempt to steal coins from another user",
        guild=discord.Object(id=guild_id)
    )
    async def steal(interaction: discord.Interaction, target: discord.Member):
        user_id = interaction.user.id
        target_id = target.id
        command_name = "steal"
        cooldown_duration = timedelta(minutes=10)

        if user_id == target_id:
            await interaction.response.send_message("You cannot steal from yourself!", ephemeral=True)
            return

        if economy.is_on_cooldown(user_id, command_name):
            remaining_time = economy.get_cooldown_time(user_id, command_name)
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            await interaction.response.send_message(
                f"⏳ You are on cooldown! Please wait {remaining_time.days} days, {hours} hours, {minutes} minutes.",
                ephemeral=True
            )
            return

        current_time = datetime.now().hour
        target_balance = economy.get_balance(target_id)
        steal_amount = random.randint(50, 300)

        if target_balance < steal_amount:
            await interaction.response.send_message(
                f"{target.display_name} doesn't have enough coins to steal from! They only have {target_balance} coins.",
                ephemeral=True
            )
            return

        if 6 <= current_time < 18:  # Daytime (6 AM - 6 PM)
            success_chance = 30  # 30% success rate during the day
        else:  # Nighttime (6 PM - 6 AM)
            success_chance = 60  # 60% success rate during the night

        roll = random.randint(1, 100)
        if roll <= success_chance:  # Successful steal
            economy.update_balance(user_id, steal_amount)
            economy.update_balance(target_id, -steal_amount)
            result = f"💸 You successfully stole {steal_amount} coins from {target.display_name}!"
            color = discord.Color.green()
        else:
            fine_amount = random.randint(20, 100) 

            caught_messages = [
                f"You tripped on {target.display_name}'s wife's bra!",
                "You stepped on a squeaky toy and alerted the guards!",
                f"You got stuck in {target.display_name}'s laundry basket.",
                "You sneezed while hiding, and everyone heard you!",
                "A cat knocked over a vase and blamed you!",
                f"While stealing, you got a call from {interaction.user.display_name}'s mom!",
                "You slipped on a banana peel and fell into the trap!",
                "You slipped on an ice cube and got covered in booboos! 🧊😭😭",
                "The security camera spotted you breakdancing in the vault!",
                f"{target.display_name}'s guard dog caught you!",
                "You tried to steal coins, but ended up stealing a cursed artifact!"
            ]

            caught_message = random.choice(caught_messages)

            result = f"🚓 {caught_message} You were caught and fined {fine_amount} coins!"
            economy.update_balance(user_id, -fine_amount)
            color = discord.Color.red()

        embed = discord.Embed(
            title="💰 Stealing Attempt",
            description=result,
            color=color
        )
        embed.set_footer(text=f"Roll: {roll}/100 (Success chance: {success_chance}%)")

        # Set cooldown after steal attempt

        await interaction.response.send_message(embed=embed)

    @bot.tree.command(
        name="daily",
        description="Get some daily money, just remember money doesn't grow on trees",
        guild=discord.Object(id=guild_id)
    )
    async def setDaily(interaction: discord.Interaction):
        user_id = interaction.user.id
        command_name = "daily"
        cooldown_duration = timedelta(days=1)
        
        if economy.is_on_cooldown(user_id, command_name):
            remaining_time = economy.get_cooldown_time(user_id, command_name)
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            await interaction.response.send_message(
                f"⏳ You are on cooldown! Please wait {remaining_time.days} days, {hours} hours, {minutes} minutes.",
                ephemeral=True
            )
            return

        reward_amount = 1000
        economy.update_balance(user_id, reward_amount)
        economy.set_cooldown(user_id, command_name, cooldown_duration)

        embed = discord.Embed(
            title="💰 Claimed Daily Balance",
            description=f"Your current balance: {economy.get_balance(user_id)} coins",
            color=discord.Color.gold()
        )
        
        await interaction.response.send_message(embed=embed)