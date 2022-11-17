import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv('token.env')

intents = discord.Intents.default()
client = commands.Bot(intents=intents, command_prefix='!', help_command=None, case_insensitive=True)

@client.listen()
async def on_ready():
    print('Logged in as {0.user}\n'.format(client))

# MESSAGES
@client.listen()
async def on_message(context):
    
    message = context.content.lower() #removes case sensitivity
    if context.author == client.user: #ignore self
        return
    if message.startswith('http'): #ignore links (GIFs)
        return

# REACTIONS
@client.listen()
async def on_reaction_add(reaction, user):

    if user == client.user: #ignore self
        return

# COMMANDS
@client.command()
async def ping(context):
    await context.send('pong!')
@client.command()
async def pong(context):
    await context.send('ping!')

TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
client.run(TOKEN)