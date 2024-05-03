# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ
"""FastAPI server for JerryBot."""
import asyncio
import os

import discord
import dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.JerryBot import JerryBot
from src.logger import Logger

dotenv.load_dotenv('tokens.env')

LOGGER = Logger('SERVER')

authToken = os.environ.get('SERVER_AUTH_TOKEN')
security = HTTPBearer()

bot = None

def authorised(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # authorise request using bearer token
    if ((authToken is not None) and (credentials.credentials != authToken)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Unauthorised')

server = FastAPI()

@server.on_event('startup')
async def startupEvent():

    global bot

    if ((TOKEN := os.environ.get('DISCORD_BOT_TOKEN')) is not None):
        bot = await JerryBot.create()
        asyncio.create_task(bot.run(TOKEN))
    else:
        LOGGER.error('Error: No token found')
        raise SystemExit

    if (authToken is None):
        LOGGER.warn('Warning: No authentication token found. Secure endpoints will not be available.')

@server.on_event('shutdown')
async def shutdownEvent():

    LOGGER.info('Server completed shutdown.')

@server.get('/test')
async def test():
    """Test endpoint to check if the server is running."""
    return ':)'

@server.get('/restart', dependencies=[Depends(authorised)])
async def restart(mode: str = 'RESTART'):
    """Restart the server."""

    LOGGER.info('Initiating server restart...')
    if (bot is not None):
        try:
            await bot.close()
        except discord.errors.DiscordException as e:
            LOGGER.error(f'Error: {e}')

    print(mode) # this communicates with the runner script to restart the server
    return { 'message': 'restarting' }

@server.get('/update', dependencies=[Depends(authorised)])
async def update():
    """Update and reboot the server."""

    LOGGER.info('Initiating server update...')
    return await restart('UPDATE')
