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
responses = [
    ['documenta', 'https://cdn.discordapp.com/attachments/901521305931747348/968570296678367272/documentary.gif'],              #Jon
    ['sea', 'https://cdn.discordapp.com/attachments/902687545857560646/1022496891658829895/download_1.gif'],                    #the sea is always right
    ['rue', 'https://tenor.com/view/key-thorin-oakenshield-all-those-who-doubted-us-rue-this-day-gif-17140731'],
    ['bronner', 'https://64.media.tumblr.com/075e4cb93cabb63d7f049ad35accaa52/tumblr_myocbow0wn1rcwa0zo1_250.gif'],             #that is what they used to call me
    [['heretic','heresy'], 'https://tenor.com/view/heretic-halo2-arbiter-grunts-gif-19621018'],
    [['traitor', 'treason'], 'https://cdn.discordapp.com/attachments/901521305931747348/901984847608811590/Heresy.gif'],        #nay, it was heresy
    ['vexor', 'https://c.tenor.com/RaG9beTFOSMAAAAC/batman-vs.gif'],                                                            #why did you say that name?
    ['jahan', 'https://tenor.com/view/legolas-the-lord-of-rings-gif-23169554'],                                                 #the white wizard
    ['die', 'https://64.media.tumblr.com/c3af27aefc0d51d80754d7b1158ae696/tumblr_moj2ur3xxU1qelmhao6_250.gif'],                 #then I shall die as one of them
    [' late', 'https://i.giphy.com/media/HVaHPyE3DUFW/giphy.webp'],                                                             #a wizard is never late
    ['one day', 'https://tenor.com/view/aragorn-but-notthis-day-lotr-gif-14120761'],                                                #but it is not this day
    [['victor', 'win', 'ftw'], 'https://64.media.tumblr.com/467b4edba8605ad6f7afe7dd5f537516/tumblr_o3gyn5GSOt1ru8yv8o2_500.gif'],  #theoden
    ['you have my ', 'https://tenor.com/view/axe-lotr-gif-5532799'],                                                                #and my axe!
    ['sand', 'https://tenor.com/view/anakin-star-wars-padme-gif-5048790'],                                                      #I hate sand
    [['potato', 'tater'], 'https://tenor.com/view/potato-po-tay-toes-lord-of-the-rings-lotr-samwise-gamgee-gif-5379028'],       #po-tay-toes
    ['mine', 'https://cdn.discordapp.com/attachments/901521305931747348/934898165709152366/resized-image-Promo.jpeg'],          #they call it a mine!   #TODO: GIF
    [['lift', 'elevator'], 'https://tenor.com/view/see-it-like-final-hamster-scared-gif-14498643'],                             #scared hamster
    ['frontflip', 'https://cdn.discordapp.com/attachments/895064046020202498/922284196871942164/ezgif-5-d8195ff3b7.gif'],       #backflip
    ['flip', 'https://tenor.com/view/trex-backflip-gif-11354213']                                                               #flip
]

@client.listen()
async def on_message(context):
    
    message = context.content.lower() #removes case sensitivity
    if context.author == client.user: #ignore self
        return
    if message.startswith('http'): #ignore links (GIFs)
        return

    #dances  
    if 'dance' in message:
        danceMoves = ['https://cdn.discordapp.com/attachments/901521305931747348/922290586487246888/ezgif-5-be2c8bfa47.gif', 'https://c.tenor.com/b2Fo3D-oA20AAAAC/dinosaur-pole-dance.gif', 'https://tenor.com/view/monty-python-and-the-holy-grail-dance-celebrate-gif-12275693', 'https://tenor.com/view/monty-python-camelot-dance-monty-python-dance-camelot-medieval-gif-17123270', 'https://tenor.com/view/katy-bentz-spin-spinny-dinosaur-gif-23363009', 'https://tenor.com/view/smeagle-gollum-gif-8750815', 'https://tenor.com/view/simba-lion-king-funny-disney-gif-5763716', 'https://tenor.com/view/skyrim-dragon-dance-elder-scrolls-gif-6076592']
        await context.channel.send(random.choice(danceMoves))
        return

    for response in responses:
        if (type(response[0]) is str):
            if (response[0] in message):
                await context.channel.send(response[1])
                return
        else:
            for prompt in response[0]:
                if (prompt in message):
                    await context.channel.send(response[1])
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