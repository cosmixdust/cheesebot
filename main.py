import discord
import random
from discord.ext import commands
from facts import cheeseFacts
from pics import cheesePhoto
from words import wordsList

intents = discord.Intents(
    message_content = True,
    messages = True
)

# This shit is neccessary but doesn't do shit too
bot = commands.Bot(command_prefix= '*', intents=intents)

@bot.event
async def on_ready():
    print('GIVE ME THE CHEESE.')
    await bot.change_presence(activity=discord.Game('cheese.'))
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

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

@bot.event
async def on_message(message):
    if any(wordsList.find(wordsList)) in message.content.lower():
        try:
            await message.add_reaction('🧀')
        except Exception as e:
            print(e)

fileToken = open("token.txt", "r")
token = fileToken.read()
bot.run(token)