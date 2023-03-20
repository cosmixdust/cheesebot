import aiosqlite
import asyncio
from datetime import datetime
import discord
import pytz
import random
import string
from discord import app_commands
from discord.ext import commands, tasks
from facts import cheeseFacts
from pics import cheesePhoto
from words import wordsList

intents = discord.Intents(
    message_content=True,
    messages=True,
    guilds=True
)

# This shit is neccessary but doesn't do shit too
bot = commands.Bot(command_prefix='*', intents=intents)


@tasks.loop(seconds=1)
async def timeCheck():
    # At given time
    now = datetime.now(pytz.utc)
    if not all((
            now.weekday() == 6,
            now.hour == 12,
            now.minute == 00)):
        return  # Time doesn't match
    # Query the database
    async with aiosqlite.connect('main.db') as db:
        async with db.execute('SELECT id FROM ids') as cursor:
            # For every result
            async for row in cursor:
                # Send to channel
                channel_id = row[0]
                channel = bot.get_partial_messageable(channel_id)
                try:
                    await channel.send('CHEESE SUNDAY.')
                except Exception as e:
                    print(e)
            await asyncio.sleep(60)

@bot.event
async def on_ready():
    # on ready stuff
    print('GIVE ME THE CHEESE.')
    await bot.change_presence(activity=discord.Game('cheese.'))
    # Connect to the database and create the 'ids' table if it doesn't exist
    async with aiosqlite.connect('main.db') as db:
        await db.execute('CREATE TABLE IF NOT EXISTS ids (id INTEGER, guild INTEGER)')
        await db.commit()
    # Start the timeCheck task
    timeCheck.start()
    # Sync commands and print the number of commands synced
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s)")


@bot.tree.command(name='cheese', description='cheese')
async def cheeseCommand(interaction: discord.Interaction):
    await interaction.response.send_message(':cheese:')


@bot.tree.command(name='fact', description='cheese fact')
async def cheeseFactCommand(interaction: discord.Interaction):
    random.shuffle(cheeseFacts)
    await interaction.response.send_message(cheeseFacts[0])


@bot.tree.command(name='pic', description='cheese pic')
async def cheesePics(interaction: discord.Interaction):
    random.shuffle(cheesePhoto)
    await interaction.response.send_message(cheesePhoto[0])


@bot.tree.command(name='announcements', description='Set a channel for announcements (admins only).')
@app_commands.describe(channel='The channel for the announcements.')
@app_commands.checks.has_permissions(administrator=True)
async def announcements(interaction: discord.Interaction, channel: discord.TextChannel):
    # Check channel is in the same guild
    if channel.guild != interaction.guild:
        return await interaction.response.send_message('That\'s not a channel on this server!', ephemeral=True)
    async with aiosqlite.connect('main.db') as db:
        cursor = await db.execute('SELECT id FROM ids WHERE guild = ?', (interaction.guild.id,))
        data = await cursor.fetchone()
        if data:
            await db.execute('UPDATE ids SET id = ? WHERE guild = ?', (channel.id, interaction.guild.id))
        else:
            await db.execute('INSERT INTO ids (id, guild) VALUES (?, ?)', (channel.id, interaction.guild.id))
        await db.commit()
    await interaction.response.send_message(f'Congrats! Your channel set for cheese announcements is now {channel.mention}')


@bot.tree.command(name='unsubscribe', description='unsub from announcements! (admins only)')
@app_commands.checks.has_permissions(administrator=True)
async def unsub(interaction: discord.Interaction):
    async with aiosqlite.connect('main.db') as db:
        cursor = await db.execute('SELECT id FROM ids WHERE guild = ?', (interaction.guild.id,))
        data = await cursor.fetchone()
        if data:
            await cursor.execute('DELETE FROM ids WHERE guild = ?', (int(interaction.guild.id),))
            await interaction.response.send_message('Got it! You will no longer recieve cheese announcements!')
        else:
            await interaction.response.send_message('You\'re not subscribed to cheese announcements!', ephemeral=True)
        await db.commit()

@bot.event
async def on_message(message):
    # trigger message stuff
    trigger_words = []
    trigger = message.content.translate(str.maketrans(
        '', '', string.punctuation)).replace('\n', '').replace(' ', '').lower()
    if not any(word in trigger for word in wordsList):
        return
    try:
        for word in wordsList:
            if word in trigger:
                trigger_words.append(word)
        if not trigger_words:
            return
        if message.author.bot:
            return
        await message.add_reaction('🧀')
        await message.author.send(f"You said: **{'**, **'.join(trigger_words)}**")
    except Exception as e:
        print(e)


fileToken = open("token.txt", "r")
token = fileToken.read()
bot.run(token)
