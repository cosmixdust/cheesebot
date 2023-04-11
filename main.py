import asyncio
import random
import typing
from datetime import datetime
import re

import aiosqlite
import pytz
import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.utils import find

from facts import cheeseFacts
from pics import cheesePhoto
from words import wordsList
from truth import cheeseTruth


intents = discord.Intents(
    message_content=True,
    messages=True,
    guilds=True,
)


bot = commands.Bot(command_prefix="*", intents=intents)

def make_intro_embed() -> discord.Embed:
    return discord.Embed(
        title="cheeseBot has joined!",
        description="What now?",
        color=discord.Color.random(),
        timestamp=datetime.now()
    ).add_field(
        name="Well...",
        value="You can start with the /help command!",
    ).add_field(
        name="And then?",
        value="Start trying out the rest of commands!",
    ).add_field(
        name="Sounds good!",
        value="We hope you enjoy cheeseBot! Stay cheesy :)"
    ).add_footer(
        text="Be advised this bot automatically sends DMs when detected. Use /blacklist to not receieve DMs."
    )


def make_help_embed(author: typing.Union[discord.User, discord.Member]) -> discord.Embed:
    return discord.Embed(
        title="About cheeseBot...",
        description="Here's everything you need to know!",
        color=discord.Color.random(),
        timestamp=datetime.now()
    ).add_field(
        name="Who am I?",
        value="I'm cheeseBot. A bot made by <@396376536070094848> related to cheese stuff.",
    ).add_field(
        name="Commands?",
        value="/cheese, /fact, /pic, /blacklist, /announcements, /truth",
    ).add_field(
        name="What's your privacy policy?",
        value="You can check our privacy policy [here](https://github.com/deltastro/cheesebot/blob/master/policy.md)"
    ).set_author(
        name=author.name,
        icon_url=author.avatar,
    )


@tasks.loop(seconds=1)
async def timeCheck():
    """
    Send "CHEESE SUNDAY." every Sunday at noon.
    """

    # At given time
    now = datetime.now(pytz.utc)
    if not all((
            now.weekday() == 6,
            now.hour == 12,
            now.minute == 00)):
        return  # Time doesn't match

    # Query the database
    async with aiosqlite.connect("main.db") as db:
        async with db.execute("SELECT id FROM ids") as cursor:

            # For every result
            async for row in cursor:

                # Send to channel
                channel_id = row[0]
                channel = bot.get_partial_messageable(channel_id)
                try:
                    await channel.send("CHEESE SUNDAY.")
                except Exception as e:
                    print(e)
    await asyncio.sleep(60)


@bot.event
async def on_ready():
    """
    Tell us when we've connected.
    """

    # on ready stuff
    print("GIVE ME THE CHEESE.")
    await bot.change_presence(activity=discord.Game("cheese."))

    # Connect to the database and create tables if they don't exist
    async with aiosqlite.connect("main.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS ids (id INTEGER, guild INTEGER)")
        await db.execute("CREATE TABLE IF NOT EXISTS blacklist (user_id INTEGER)")
        await db.commit()

    # Start the timeCheck task
    timeCheck.start()

    # Sync commands and print the number of commands synced
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s)")

@bot.event
async def on_guild_join(guild):
    """
    Message that bot sends when it joins a server.
    """
    general = find(lambda x: x.name == 'general', guild.text_channels)
    if general and general.permissions_for(guild.me).send_messages:
        await general.send(embed=make_intro_embed())


@bot.tree.command(name="help")
async def helpCommand(interaction: discord.Interaction):
    """
    use this to know more
    """

    await interaction.response.send_message(embed=make_help_embed(interaction.user))


@bot.tree.command(name="cheese")
async def cheeseCommand(interaction: discord.Interaction):
    """
    cheese
    """

    await interaction.response.send_message("\N{CHEESE WEDGE}")


@bot.tree.command(name="fact")
async def cheeseFactCommand(interaction: discord.Interaction):
    """
    cheese fact
    """

    await interaction.response.send_message(random.choice(cheeseFacts))


@bot.tree.command(name="pic")
async def cheesePics(interaction: discord.Interaction):
    """
    cheese pic
    """

    await interaction.response.send_message(random.choice(cheesePhoto))

@bot.tree.command(name="truth")
async def cheeseOfTruth(interaction: discord.Interaction):
    """
    the cheese of truth
    """
    
    await interaction.response.send_message(random.choice(cheeseTruth))


@bot.tree.command(name="blacklist")
async def blackList(interaction: discord.Interaction):
    """
    Blacklist yourself from the trigger DMs (using the command again will whitelist you.)
    """

    async with aiosqlite.connect("main.db") as db:
        cursor = await db.execute(
            "SELECT user_id FROM blacklist WHERE user_id = ?",
            (interaction.user.id,),
        )
        data = await cursor.fetchone()
        if data:
            await db.execute(
                "DELETE FROM blacklist WHERE user_id = ?",
                (interaction.user.id,),
            )
            message = "You have been removed from the blacklist. You will now receive DMs."
        else:
            await db.execute(
                "INSERT INTO blacklist (user_id) VALUES (?)",
                (interaction.user.id,),
            )
            message = "You have been added to the blacklist. You will no longer receive DMs."
        await db.commit()
    await interaction.response.send_message(message)
    

@bot.tree.command(name="announcements")
@app_commands.describe(channel="The channel for the announcements.")
@app_commands.checks.has_permissions(administrator=True)
async def manage_announcements(interaction: discord.Interaction, channel: typing.Optional[discord.TextChannel] = None):
    """
    Set a channel for announcements (admins only).
    """

    assert interaction.guild
    async with aiosqlite.connect("main.db") as db:
        cursor = await db.execute(
            "SELECT id FROM ids WHERE guild = ?",
            (interaction.guild.id,),
        )
        data = await cursor.fetchone()
        if not channel:

            # Unsubscribe from announcements
            if data:
                await cursor.execute(
                    "DELETE FROM ids WHERE guild = ?",
                    (interaction.guild.id,),
                )
                await interaction.response.send_message(
                    "Got it! You will no longer receive cheese announcements!"
                )
            else:
                await interaction.response.send_message(
                    "You're not subscribed to cheese announcements!",
                    ephemeral=True,
                )
        else:

            # Subscribe to announcements
            if channel.guild != interaction.guild:
                return await interaction.response.send_message("That's not a channel on this server!", ephemeral=True)
            if data:
                await db.execute(
                    "UPDATE ids SET id = ? WHERE guild = ?",
                    (channel.id, interaction.guild.id),
                )
            else:
                await db.execute(
                    "INSERT INTO ids (id, guild) VALUES (?, ?)",
                    (channel.id, interaction.guild.id),
                )
            await interaction.response.send_message(
                (
                    f"Congrats! Your channel set for cheese announcements "
                    f"is now {channel.mention}"
                )
            )
        await db.commit()


# no_cheese = r"""[\s!"£$%^&*()\[\]{}'@#~;:,<.>\/?\-\\\|`¬]"""
no_cheese = r"""[\s!"'\-,.?]*"""
cheese_regex = re.compile(
    "({0})".format("|".join([
        "(?:" + "".join([p + no_cheese for p in re.escape(i)]) + ")"
         for i in wordsList
    ])),
    re.IGNORECASE | re.DOTALL
)


def check_content_for_cheese(content: str) -> typing.Optional[str]:
    """
    Check a string for if it contains any cheese keywords. If it does, then the
    message content with the flagged keywords in bold is returned, otherwise
    None.

    Parameters
    ----------
    content : str
        The content that you want to check.

    Returns
    -------
    str | None
        The flagged content, or ``None``.
    """

    changed = cheese_regex.sub("**\\1**", content)
    if changed == content:
        return None
    return changed


@bot.event
async def on_message(message: discord.Message):
    """
    Look for a message being sent, see if it contains cheese.
    """

    if message.author.bot:
        return
    cheese_content = check_content_for_cheese(message.content)
    if cheese_content is None:
        return
    send_dm: bool = True
    async with aiosqlite.connect("main.db") as db:
        async with db.execute("SELECT user_id FROM blacklist") as cursor:
            async for row in cursor:
                if row[0] == message.author.id:
                    send_dm = False
    await message.add_reaction("🧀")
    if not send_dm:
        return False

    embed = discord.Embed(
        title="Cheese Detected!",
        # description=f"You said: **{cheese_content}**",
        description=cheese_content,
        color=discord.Color.random(),
        timestamp=datetime.now()
    ).set_footer(
        text="Use /blacklist to not receive DMs anymore",
    )
    await message.author.send(embeds=[embed])


fileToken = open("token.txt", "r")
token = fileToken.read()
bot.run(token)