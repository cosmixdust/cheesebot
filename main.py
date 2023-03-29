import aiosqlite
import asyncio
import discord
import pytz
import random
import string
import typing
from datetime import datetime
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

def make_help_embed(author: discord.User) -> discord.Embed:
    embed = discord.Embed(
        title='About cheeseBot...',
        description='Here\'s everything you need to know!',
        color=discord.Color.random(),
        timestamp=datetime.now()
    )
    embed.add_field(
        name='Who am I?',
        value='I\'m cheeseBot. A bot made by <@!396376536070094848> related to cheese stuff.',
    )
    embed.add_field(
        name='Commands?',
        value='/cheese, /fact, /pic, /blacklist, /announcements, /unsubscribe'
    )
    embed.set_author(
        name=author.name,
        icon_url=author.avatar,
    )
    return embed


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
    # Connect to the database and create tables if they don't exist
    async with aiosqlite.connect('main.db') as db:
        await db.execute('CREATE TABLE IF NOT EXISTS ids (id INTEGER, guild INTEGER)')
        await db.execute('CREATE TABLE IF NOT EXISTS blacklist (user_id INTEGER)')
        await db.commit()
    # Start the timeCheck task
    timeCheck.start()
    # Sync commands and print the number of commands synced
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s)")

@bot.tree.command(name='help', description='use this to know more')
async def helpCommand(interaction: discord.Interaction):
    await interaction.response.send_message(embed=make_help_embed(interaction.user))

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

@bot.tree.command(name='blacklist', description='blacklist yourself from the trigger DMs (using the command again will whitelist you.)')
async def blackList(interaction: discord.Interaction):
    async with aiosqlite.connect('main.db') as db:
        cursor = await db.execute('SELECT user_id FROM blacklist WHERE user_id = ?', (int(interaction.user.id),))
        data = await cursor.fetchone()
        if data:
            await db.execute('DELETE FROM blacklist WHERE user_id = ?', (int(interaction.user.id),))
            message = 'You have been removed from the blacklist. You will now receive DMs.'
        else:
            await db.execute('INSERT INTO blacklist (user_id) VALUES (?)', (int(interaction.user.id),))
            message = 'You have been added to the blacklist. You will no longer receive DMs.'
        await db.commit()
    await interaction.response.send_message(message)
    

@bot.tree.command(name='announcements', description='Set a channel for announcements (admins only).')
@app_commands.describe(channel='The channel for the announcements.')
@app_commands.checks.has_permissions(administrator=True)
async def manage_announcements(interaction: discord.Interaction, channel: typing.Optional[discord.TextChannel] = None):
    async with aiosqlite.connect('main.db') as db:
        cursor = await db.execute('SELECT id FROM ids WHERE guild = ?', (interaction.guild.id,))
        data = await cursor.fetchone()
        if not channel:
            # Unsubscribe from announcements
            if data:
                await cursor.execute('DELETE FROM ids WHERE guild = ?', (interaction.guild.id,))
                await interaction.response.send_message('Got it! You will no longer receive cheese announcements!')
            else:
                await interaction.response.send_message('You\'re not subscribed to cheese announcements!', ephemeral=True)
        else:
            # Subscribe to announcements
            if channel.guild != interaction.guild:
                return await interaction.response.send_message('That\'s not a channel on this server!', ephemeral=True)
            if data:
                await db.execute('UPDATE ids SET id = ? WHERE guild = ?', (channel.id, interaction.guild.id))
            else:
                await db.execute('INSERT INTO ids (id, guild) VALUES (?, ?)', (channel.id, interaction.guild.id))
            await interaction.response.send_message(f'Congrats! Your channel set for cheese announcements is now {channel.mention}')
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
        async with aiosqlite.connect('main.db') as db:
            async with db.execute('SELECT user_id FROM blacklist') as cursor:
                async for row in cursor:
                    if row[0] == message.author.id:
                        await message.add_reaction('🧀')
                        return
        await message.add_reaction('🧀')
        trigger_words_str = '**, **'.join(trigger_words)
        embed = discord.Embed(
            title='Triggered Words Detected',
            description=f"You said: **{trigger_words_str}**",
            color=discord.Color.random(),
            timestamp=datetime.now()
        )
        embed.set_author(
            name=message.author.name,
            icon_url=message.author.avatar,
        )
        embed.set_footer(text="Use /blacklist to not receive DMs anymore")
        await message.author.send(embed=embed)
    except Exception as e:
        print(e)


fileToken = open("token.txt", "r")
token = fileToken.read()
bot.run(token)
