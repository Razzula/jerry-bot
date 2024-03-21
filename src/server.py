# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ
"""FastAPI server for JerryBot."""
import asyncio
from contextlib import asynccontextmanager
import os

import dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from JerryBot import JerryBot

dotenv.load_dotenv('token.env')

authToken = os.environ.get('AUTH_TOKEN')
security = HTTPBearer()

def authorised(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if ((authToken is not None) and (credentials.credentials != authToken)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

@asynccontextmanager
async def lifespan(app: FastAPI):

    global bot

    if ((TOKEN := os.environ.get('DISCORD_BOT_TOKEN')) is not None):
        bot = await JerryBot.create()
        asyncio.create_task(bot.run(TOKEN))
    else:
        print('Error: No token found')
        raise SystemExit

    if (authToken is None):
        print('Warning: No authentication token found. Secure endpoints will not be available.')

    yield # Run the application

    print('Server completed shutdown')

app = FastAPI(lifespan=lifespan)

@app.get("/test")
async def test():
    """Test endpoint to check if the server is running."""
    return ":)"

@app.get("/restart", dependencies=[Depends(authorised)])
async def restart():
    """Restart the server."""
    return {"message": "TODO"}

@app.get("/update", dependencies=[Depends(authorised)])
async def update():
    """Update and reboot the server."""
    return {"message": "TODO"}

@app.get("/exit", dependencies=[Depends(authorised)])
async def exit():
    """Terminate the server."""
    return {"message": "TODO"}
