import asyncio
import dotenv
import os

from src.JerryBot import JerryBot

dotenv.load_dotenv('tokens.env')

def update():
    pass

async def start():
    if ((TOKEN := os.environ.get('DISCORD_BOT_TOKEN')) is not None):
        bot = await JerryBot.create(update)
        await bot.run(TOKEN)

asyncio.run(start())
