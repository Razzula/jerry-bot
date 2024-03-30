# jerry-bot

A Discord bot written in Python, using the Discord.py library.

## Overview

### Modules

This bot is designed to be modular, with each module being able to be enabled or disabled at runtime. The bot is designed to be run on a server, and can be controlled via a web interface.

This program consists primarly of three modules:
- `JerryBot.py` - The main bot module. This module is responsible for handling the Discord bot and its interactions.
- `server.py` - The server module. This module is responsible for handling the HTTP server that listens for incoming requests.
- `runner.py` - The entry point for the application. This module handles the lifecycle of the bot and server, using health checks and automated restarts and updates.

### Cogs

The bot is split into cogs, which are individual components that can be enabled or disabled at runtime. Each cog is responsible for a different set of commands or events. These are defined and configured in the `__init__` method of the `JerryBot` class.

Included are:
 - **JerryCoreCog** - The core cog (defined within `JerryBot.py`), which contains the basic generic commands and events for a bot.
 - **JerryCog** - The main cog, which contains Jerry-centric behaviours.
 - **SteamCog** - A cog that contains commands for interacting with the Steam API.
 - **TagCog** - A cog that contains commands for hosting a game of tag.

## Installation

### Prerequisites

1. Python 3.8.5 or later is required to run this bot.
    - The required Python packages can be installed using `pip install -r requirements.txt`.

2. Your own Discord bot is required to run this.
    - You can create a new bot at the [Discord Developer Portal](https://discord.com/developers/applications).
    - For full functionality, the bot requires the following permissions:
        - Read Messages
        - Send Messages
        - Add Reactions
        - Manage Roles
        - Manage Messages
        - Embed Links
        - Use External Emojis
    - The bot requires the following privileged gateway intents:
        - Presence Intent
        - Server Members Intent
        - Message Content Intent

3. As well as storing data in an SQLite3 file, this bot also uses Redis for caching. Redis is only available on Linux. If you are planning to run this bot on Windows, you can use WSL2 or a VM to run the bot on a Linux environment. This step is optional, but recommended for better performance.
    - `sudo apt-get install redis-server`

### Configuration

This bot requires a `tokens.env` file in the root directory of the project. This file should contain the following environment variables:

- `DISCORD_BOT_TOKEN` - The token of your Discord bot. You can get this from the [Discord Developer Portal](https://discord.com/developers/applications).
- `STEAM_API_KEY` - In order to make use of functions that interact with the Steam API, you will need a key. You can get this from the [Steam Developer Portal](https://steamcommunity.com/dev/apikey).
- `SERVER_AUTH_TOKEN` - A secret token that is used to authenticate requests to the server. This is only required if you are planning to use the server module.

Additionally, you can set:
- `DEBUG = 1` - This will enable debug mode, which will prevent some excess calls (such as updating the bot's profile picture on every startup), and set the uvicorn server to reload on changes.

If there is an error launching the server, the runner will use Discord's Webhook API to send an error message to a specified channel. To configure this, you will need to insert IDs of any WebHooks you wish to utilise in the database. Currently this is a manual step (the table will be created automatically by the runner).
```sql
INSERT INTO emergencyContacts (webhookID) VALUES ('<webhook_id>');
```

#### CI/CD

GitHub Actions can be setup to automatically deploy the bot to a server (such as an RPi) on every push to the master branch. This can be done by making a GET request to the server's `/update` endpoint, which will pull the latest changes from the repository and restart the bot. (Note: this requires a valid bearer token).

## Usage

### Running

To run the bot, simply run `runner.py` using Python.

However, you can also run the bot without the runner by using `uvicorn server:app ...` directly. Or, you can instantiate and use the `JerryBot` class directly for more lightweight usage of just the sole bot.

The `/setup` directory provides a script to setup the bot for a Linux server, using systemctl to manage the bot as a service.

The default prefix for the bot is `!`, but this can be changed in the `JerryBot` class.

### Commands

The bot has a number of commands that can be used in Discord. These are defined in the cogs, and can be enabled or disabled at runtime.

#### JerryCoreCog
- `!help`: Displays a list of commands and their descriptions. Passing a command as an argument will display more information about that command.
- `!ping`, `!pong`: Pings the bot.
- `!version`: Displays the current version of the bot.

#### JerryCog
This cog handles 'soft commands' (commands that are triggered by messages, rather than being explicitly called). The bot will also react with GIFs and emotes to certain messages.

The following commands are available:

- `!party`: Dance!
    - (This command is also triggered whenever a message contains the word 'dance')
- `!pick`: Randomly select a choice from a list of options.
- `!roll`: Roll a die.
- `!bonk`: Bonk a user (and send them to bonk jail).
- `!summon`: Summon a user to the voice channel.
    - (This command is also triggered whenever a message contains the word 'summon', using the `remind` command.)
- `remind`: Set a reminder for a user.
    - This command is triggered by having a message that contains the word 'remind' followed by a time and a message.

#### SteamCog
- `!steam`: Interacts with the Steam API. This command has subcommands:
    - `!steam <id>` - Sets the Steam ID of the user.
    - `!steam` - Gets Steam information about the user.
- `!game`: Selects a random game from a user's Steam Library.
- `!hunt`: Challenge a user to pursue an achievement from their current Steam game.
- `!quarry`: Display the current hunt target.

#### TagCore
This cog does not utilise any commands, but instead just listens for messages, and trasnfers a role called `It` to the user who is tagged.