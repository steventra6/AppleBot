import discord
from discord.ext import commands
import random
import discord.app_commands as app_commands
from discord.ui import View, Select
from datetime import timedelta
import gamble

async def setup_gambling_games(bot, economy: gamble.Economy, guild_id: str):
    
    @bot.tree.command(
        name="coinflip",
        description="Flip a coin! Bet on heads or tails",
        guild=discord.Object(id=guild_id)
    )
    @app_commands.describe(bet="The amount of coins to bet", choice="Your guess: heads or tails")
    @app_commands.choices(
        choice=[
            app_commands.Choice(name="Heads", value="heads"),
            app_commands.Choice(name="Tails", value="tails")
        ]
    )
    async def coinflip(interaction: discord.Interaction, bet: int, choice: str):
        user_id = interaction.user.id
        current_balance = economy.get_balance(user_id)
        command_name = "coinflip"
        
        if economy.is_on_cooldown(user_id, command_name):
            remaining_time = economy.get_cooldown_time(user_id, command_name)
            await interaction.response.send_message(f"You're on cooldown! Try again in {remaining_time}.", ephemeral=True)
            return
        
        if bet <= 0 or bet > current_balance:
            await interaction.response.send_message("Invalid bet amount!", ephemeral=True)
            return
        
        flip_result = random.choice(["heads", "tails"])
        winnings = bet * 2 if flip_result == choice.lower() else -bet
        economy.update_balance(user_id, winnings)
        result_message = f"The coin landed on {flip_result}! {'You won!' if winnings > 0 else 'You lost!'} New balance: {economy.get_balance(user_id)}"
        
        embed = discord.Embed(title="Coin Flip", description=result_message, color=discord.Color.gold() if winnings > 0 else discord.Color.red())
        economy.set_cooldown(user_id, command_name, timedelta(seconds=10))
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(
        name="roll",
        description="Roll a dice! Bet on the outcome of a d6 roll",
        guild=discord.Object(id=guild_id)
    )
    async def roll(interaction: discord.Interaction, bet: int, guess: int):
        user_id = interaction.user.id
        current_balance = economy.get_balance(user_id)
        command_name = "roll"
        
        if economy.is_on_cooldown(user_id, command_name):
            remaining_time = economy.get_cooldown_time(user_id, command_name)
            await interaction.response.send_message(f"You're on cooldown! Try again in {remaining_time}.", ephemeral=True)
            return
        
        if bet <= 0 or bet > current_balance:
            await interaction.response.send_message("Invalid bet amount!", ephemeral=True)
            return
        
        if guess < 1 or guess > 6:
            await interaction.response.send_message("Invalid guess! Guess a number between 1 and 6.", ephemeral=True)
            return
        
        dice_roll = random.randint(1, 6)
        winnings = bet * 5 if dice_roll == guess else -bet
        economy.update_balance(user_id, winnings)
        result_message = f"The dice landed on {dice_roll}! {'You won!' if winnings > 0 else 'You lost!'} New balance: {economy.get_balance(user_id)}"
        
        embed = discord.Embed(title="Dice Roll", description=result_message, color=discord.Color.gold() if winnings > 0 else discord.Color.red())
        economy.set_cooldown(user_id, command_name, timedelta(seconds=10))
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(
        name="lottery",
        description="Enter a lottery with a chance to win big!",
        guild=discord.Object(id=guild_id)
    )
    async def lottery(interaction: discord.Interaction, bet: int):
        user_id = interaction.user.id
        current_balance = economy.get_balance(user_id)
        command_name = "lottery"
        
        if economy.is_on_cooldown(user_id, command_name):
            remaining_time = economy.get_cooldown_time(user_id, command_name)
            await interaction.response.send_message(f"You're on cooldown! Try again in {remaining_time}.", ephemeral=True)
            return
        
        if bet <= 0 or bet > current_balance:
            await interaction.response.send_message("Invalid bet amount!", ephemeral=True)
            return
        
        jackpot = random.randint(1000, 5000)
        winnings = jackpot if random.randint(1, 100) <= 10 else -bet  # 10%
        economy.update_balance(user_id, winnings)
        result_message = f"You {'won the jackpot!' if winnings > 0 else 'lost!'} New balance: {economy.get_balance(user_id)}"
        
        embed = discord.Embed(title="Lottery", description=result_message, color=discord.Color.gold() if winnings > 0 else discord.Color.red())
        economy.set_cooldown(user_id, command_name, timedelta(seconds=10))
        await interaction.response.send_message(embed=embed)
