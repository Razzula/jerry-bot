# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ
"""Main module to run the FastAPI server."""
import asyncio
from enum import Enum
import json
import os
import signal
import subprocess
from threading import Thread
import textwrap
from typing import Final

import dotenv
import httpx

from DatabaseManager import DatabaseManager
from logger import Logger

dotenv.load_dotenv('tokens.env')

logger = Logger('RUNNER')

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
                    return True, result.get(resultKey, True)
                return True, None
            return False, response.status_code
        except httpx.RequestError:
            return False, None

class ServerStatus(Enum):
    """Status of the server."""

    COLD = 0
    RUNNING = 1
    UPDATE = 2
    RESTART = 3
    ERROR = 4

class Server:
    """Class to manage the FastAPI server."""

    def __init__(self):
        self.process = None
        self.status = ServerStatus.COLD

    def serve(self):
        """Start the FastAPI server."""

        command = ['uvicorn', 'src.server:server', '--host', '0.0.0.0', '--port', '8000']
        if (os.environ.get('DEBUG') == 'True'):
            command.append('--reload')
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)

    def kill(self, status: ServerStatus = ServerStatus.RESTART):
        """Kill the FastAPI server."""

        self.process.send_signal(signal.SIGTERM)
        self.process.wait()
        self.status = status

    def monitor(self):
        """
        Reads the process output line by line and checks for the terminationSignal.
        If found, it returns True to indicate the server should be stopped.
        """
        while True:
            output = self.process.stdout.readline()

            match output.strip():
                case 'RESTART':
                    self.kill(ServerStatus.RESTART)
                case 'UPDATE':
                    self.kill(ServerStatus.UPDATE)
                case _:
                    print(output, end='')  # display the output

            if (self.process.poll() is not None):  # process has terminated
                break

    def getStatus(self):
        """Return the status of the server."""

        return self.status

    def __del__(self):
        """Kill the FastAPI server when the object is deleted."""

        if (self.process is not None):
            self.kill()

async def runner():
    """Run the FastAPI server, with health checks."""

    # setup
    logger.info('Starting runner...')

    DB_MANAGER.executeOneshot('''
        CREATE TABLE IF NOT EXISTS emergencyContacts (
            webhookID VARCHAR(19) PRIMARY KEY
        )
    ''')

    # main loop
    while (True):

        # first, ping an external serviceto ensure that internet connection is available
        connection, result = await ping('https://discord.com/api/v9/users/@me', auth=DISCORD_BOT_TOKEN, resultKey='id')
        if (connection is False):
            match result:
                case None:
                    logger.error('Error: Internet connection not available.')
                case _:
                    logger.error(f'Error: Discord API returned {result}.')
            return

        botID = result

        # then, run the FastAPI server
        server = Server()
        thread = Thread(target=server.monitor)
        logger.info('Starting server...')
        server.serve()
        thread.start()

        # then, perform a health check on the server
        await asyncio.sleep(10)
        if (not await ping('http://localhost:8000/test')):
            logger.error('Error: Server is not running.')

            await alert(textwrap.dedent(f'''\
                Hear ye, hear ye! It is with a heavy heart and a slightly unsteady hand (the mead this evening was particularly potent) that I must relay the most unfortunate tidings. Our beloved sovereign, <@{botID}>, in a turn of events as unforeseen as it is calamitous, has succumbed to the wiles of an insidious well and has thus descended into its abyssal depths with all the grace of a leaden feather.

                Our finest digital blacksmiths will hoist His Majesty from his unplanned subterranean excursion, as soon as possible.

                May your spirits remain high during these trying times. Now, if you'll excuse me, I must attend to... something. Ah, yes, another flagon! For courage, of course.'''
            ))
            return

        thread.join() # wait for the server to finish
        result = server.getStatus()
        if (result == ServerStatus.UPDATE):
            logger.info('Server stopped. Update required.')
            update()
            logger.info('Update complete. Restarting...')
        else:
            logger.info('Server stopped. Restarting...')

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
                logger.error(f'Failed to sending webhook to {webhookID}: {response.status_code}')

def update():
    """Update the server."""

    subprocess.run(['git', 'pull'], check=True)
    # TODO: pip install -r requirements.txt
    # really, this should use a bash script to do the update

if (__name__ == '__main__'):

    asyncio.run(runner())
