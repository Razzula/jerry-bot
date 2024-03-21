# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ
"""Main module to run the FastAPI server."""
import asyncio
import multiprocessing
import os
import subprocess
from threading import Thread

import dotenv
import httpx
from uvicorn import Config, Server

dotenv.load_dotenv('token.env')

async def ping(address: str):
    """Ping an address to check if it is reachable."""

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(address)
            return (response.status_code == 200)
        except httpx.RequestError:
            return False

def serve():
    """Start the FastAPI server."""
    config = Config("server:app", host="0.0.0.0", port=8000, reload=os.environ.get('DEBUG'))
    server = Server(config)
    server.run()

async def runner():
    """Run the FastAPI server, with health checks."""

    while (True):

        # first, ping an external serviceto ensure that internet connection is available
        if (not await ping('https://www.example.com')):
            print('Error: Internet connection not available.')
            return

        # then, run the FastAPI server
        thread = Thread(target=serve)
        thread.start()

        # then, perform a health check on the server
        await asyncio.sleep(10)
        if (not await ping('http://localhost:8000/test')):
            print('Error: Server is not running.')
            return

        thread.join() # wait for the server to finish

if (__name__ == '__main__'):
    asyncio.run(runner())
