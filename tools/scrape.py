# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ
"""_summary_"""
import json
import os
import sys
import discord
import dotenv

CLIENT = discord.Client(intents=discord.Intents.all())

@CLIENT.event
async def on_ready():
    """_summary_"""
    print(f'Logged in as {CLIENT.user}')
    await scrapeMessages(CHANNEL_ID, MESSAGE_LIMIT, SCRAPE_OLDEST_FIRST)
    await CLIENT.close()

async def scrapeMessages(channelID, messageLimit, scrapeOldestFirst):
    """_summary_

    Args:
        channelID (_type_): _description_
        messageLimit (_type_): _description_
        scrapeOldestFirst (_type_): _description_
    """
    channel = CLIENT.get_channel(channelID)
    guildId = str(channel.guild.id)
    if not channel:
        print(f'Could not find channel with ID {channelID}')
        return

    count = 0
    messages = []

    users = {}

    try:

        async for message in channel.history(limit=messageLimit, oldest_first=scrapeOldestFirst):

            # metrics
            if (count % 1000 == 0 and count > 0):
                print(f'{int(count / 1000)}k...')
            count += 1

            # track metadata
            if (not users.get(message.author.id)):
                users[message.author.id] = message.author.name

            if (message.content == ''): # ignore empty messages
                continue

            reactions = {}
            if (message.reactions):
                for reaction in message.reactions:
                    emote = reaction.emoji if isinstance(reaction.emoji, str) else reaction.emoji.name
                    reactors = []
                    async for user in  reaction.users():
                        reactors.append(user.id)
                        if (not users.get(user.id)):
                            users[user.id] = user.name
                reactions[emote] = reactors

            temp = {
                'id': message.id,
                'date': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'author': message.author.id,
                'content': message.content or message.system_content,
            }

            if (reactions):
                temp['reactions'] = reactions

            # TODO
            # - handle embeds

            messages.append(temp)

    except discord.Forbidden:
        print('Error: Bot does not have permissions to read message history in this channel.')
    except discord.HTTPException as e:
        print(f'Error: Coudl not fetch messages due to an HTTP error: {e}')

    print(f'Fetched {len(messages)} (of {count}) messages')
    messages = sorted(messages, key=lambda x: x['date']) # order by date, so that output is indiscriminant of scrape order

    # write data
    serverDirectory = os.path.join(DATA_DIRECTORY, guildId)
    if (not os.path.exists(serverDirectory)):
        os.makedirs(serverDirectory)

    with open(os.path.join(serverDirectory, f'{channelID}.json'), 'w', encoding='utf-8') as file:
        json.dump(
            {
                'metadata': {
                    'users': users
                },
                'messages': messages,
            }
            , file, ensure_ascii=False, indent=4
        )
    print('Done.')

dotenv.load_dotenv('token.env')
DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), 'data')

if (__name__ == "__main__"):

    if (len(sys.argv) < 2):
        print("Error: Please provide the channel ID as a parameter.")
        sys.exit(1)

    CHANNEL_ID = int(sys.argv[1])
    MESSAGE_LIMIT = int(sys.argv[2]) if len(sys.argv) >= 3 else None
    SCRAPE_OLDEST_FIRST = bool(sys.argv[3]) if len(sys.argv) >= 4 else False

    if ((TOKEN := os.environ.get('DISCORD_BOT_TOKEN')) is not None):
        CLIENT.run(TOKEN)
    else:
        print('Error: No token found')
