# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ
"""Main module to run the FastAPI server."""
import asyncio
import json
import multiprocessing
import os
import subprocess
from threading import Thread
import textwrap
from typing import Final

import dotenv
import httpx
from uvicorn import Config, Server

from DatabaseManager import DatabaseManager

dotenv.load_dotenv('tokens.env')

DYNAMIC_DATA_PATH: Final[str] = 'data/dynamic/'
WEBHOOK_TOKEN = os.environ.get('WEBHOOK_TOKEN')
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

DB_MANAGER = DatabaseManager(os.path.join(DYNAMIC_DATA_PATH, 'global.db'))

async def ping(address: str, auth: str | None = None, resultKey: str | None = None):
    """Ping an address to check if it is reachable."""

    headers = {}
    if (auth is not None):
        headers['Authorization'] = f'Bot {DISCORD_BOT_TOKEN}'

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(address, headers=headers)
            if (response.status_code == 200):
                if (resultKey is not None):
                    result = json.loads(response.text)
                    return result.get(resultKey, True)
                return True
        except httpx.RequestError:
            return False
        
    return False

def serve():
    """Start the FastAPI server."""
    config = Config('server:app', host='0.0.0.0', port=8000, reload=os.environ.get('DEBUG'))
    server = Server(config)
    server.run()

async def runner():
    """Run the FastAPI server, with health checks."""

    # setup
    print('Starting runner...')

    DB_MANAGER.executeOneshot('''
        CREATE TABLE IF NOT EXISTS emergencyContacts (
            webhookID VARCHAR(19) PRIMARY KEY
        )
    ''')

    # main loop
    while (True):

        # first, ping an external serviceto ensure that internet connection is available
        if ((botID := await ping('https://discord.com/api/v9/users/@me', auth=DISCORD_BOT_TOKEN, resultKey='id')) is False):
            print('Error: Internet connection not available.')
            return

        # then, run the FastAPI server
        thread = Thread(target=serve)
        print('Starting server...')
        thread.start()

        # then, perform a health check on the server
        # await asyncio.sleep(10)
        if (not await ping('http://localhost:8000/test')):
            print('Error: Server is not running.')

            await alert(textwrap.dedent(f'''\
                Hear ye, hear ye! It is with a heavy heart and a slightly unsteady hand (the mead this evening was particularly potent) that I must relay the most unfortunate tidings. Our beloved sovereign, <@{botID}>, in a turn of events as unforeseen as it is calamitous, has succumbed to the wiles of an insidious well and has thus descended into its abyssal depths with all the grace of a leaden feather.
                
                Our finest digital blacksmiths will hoist His Majesty from his unplanned subterranean excursion, as soon as possible.
                
                May your spirits remain high during these trying times. Now, if you'll excuse me, I must attend to... something. Ah, yes, another flagon! For courage, of course.'''
            ))
            return

        thread.join() # wait for the server to finish

async def alert(message: str):
    """Alert the user that the server is running."""
    
    databaseManager = DatabaseManager(os.path.join(DYNAMIC_DATA_PATH, 'global.db'))
    emegrencyContacts = databaseManager.executeOneshot('SELECT webhookID FROM emergencyContacts')

    for contact in emegrencyContacts:
        await sendWebhook(contact[0], message)

async def sendWebhook(webhookID: str, message: str):
    """Send a message to a Discord webhook."""
    
    if ((webhookID is not None) and (message is not None)):

        url = f'https://discord.com/api/webhooks/{webhookID}/{WEBHOOK_TOKEN}'
        payload = {'content': message}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            
            if (response.status_code not in [200, 204]):
                print(f'Failed to sending webhook to {webhookID}: {response.status_code}')

if (__name__ == '__main__'):

    asyncio.run(runner())
