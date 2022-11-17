import os, random
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
from dotenv import load_dotenv

load_dotenv('token.env')

# GLOBALS
intents = discord.Intents.default()
intents.members = True
client = commands.Bot(intents=intents, command_prefix='!', help_command=None, case_insensitive=True)

botsChannel = None

@client.listen()
async def on_ready():
    print('Logged in as {0.user}\n'.format(client))

# MESSAGES
responses = [
    [['for the alliance', 'for the king'], 'https://tenor.com/view/halo-halo2-halo-oorah-gif-15782884'],                        #hoorah
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
reactions = [
    #flags
    ['alliance', '<:theAlliance:899087916251353118>'],
    ['argentin', '🇦🇷'],
    [['canada', 'canhead'], '🇨🇦'],
    [['australia', 'didgeridumdum'], '🇦🇺'],
    [['new zealand', 'kiwi'], '🇳🇿'],
    [['malta', 'maltesers'], '🇲🇹'],
    #jerry
    ['doubt', '<:doubt:922292403627491378>'],
    ['jerry', '❤️'],
    ['beans', '<:beans:796047923711836210>'],
]

@client.listen()
async def on_message(context):
    
    message = context.content.lower() #removes case sensitivity
    if context.author == client.user: #ignore self
        return
    if message.startswith('http'): #ignore links (GIFs)
        return

    #bonk
    if 'jerry' in message and 'bonk' in message:
        keynote = None
        if '<@!' in str(message):
            keynote = '!'
        elif '<@' in str(message):
            keynote = '@'

        if (keynote != None):

            #get target id
            msg = str(message)
            temp = ''
            flag = False
            for i in range(len(msg)):
                if msg[i] == keynote:
                    flag = True
                    continue
                if flag:
                    if msg[i] == '>':
                        break
                    else:
                        temp += msg[i]
            id = int(temp)
            await bonk(context, f'<@{id}>')

    #dance
    if 'dance' in message:
        danceMoves = ['https://cdn.discordapp.com/attachments/901521305931747348/922290586487246888/ezgif-5-be2c8bfa47.gif', 'https://c.tenor.com/b2Fo3D-oA20AAAAC/dinosaur-pole-dance.gif', 'https://tenor.com/view/monty-python-and-the-holy-grail-dance-celebrate-gif-12275693', 'https://tenor.com/view/monty-python-camelot-dance-monty-python-dance-camelot-medieval-gif-17123270', 'https://tenor.com/view/katy-bentz-spin-spinny-dinosaur-gif-23363009', 'https://tenor.com/view/smeagle-gollum-gif-8750815', 'https://tenor.com/view/simba-lion-king-funny-disney-gif-5763716', 'https://tenor.com/view/skyrim-dragon-dance-elder-scrolls-gif-6076592']
        await context.channel.send(random.choice(danceMoves))
        return

    #react to message
    for reaction in reactions:
        if (type(reaction[0]) is str):
            if (reaction[0] in message):
                try:
                    await context.add_reaction(reaction[1])
                except discord.errors.HTTPException:
                    print(f'Error: Unknown Emoji ({reaction[1]})')
        else:
            for prompt in reaction[0]:
                if (prompt in message):
                    try:
                        await context.add_reaction(reaction[1])
                    except discord.errors.HTTPException:
                        print(f'Error: Unknown Emoji ({reaction[1]})')
                    break

    #words of wisdom
    if 'jerry' in message and 'wis' in message:
        try:
            file = open('fortune.txt', 'r')
            options = []
            for line in file:
                line = line.rstrip() + ' '
                if line != ' ' and line[0] != '#':
                    options.append(line)

            l = len(options) - 1
            n = random.randint(0, l)
            if "{}" in options[n]:
                options[n] = options[n].format("<@" + str(context.author.id) + ">")
            await context.channel.send(options[n])
            return
        except IOError:
            print("Error: fortune.txt is blank")
        await context.channel.send("Hmm. I can't think of anything... 🤔")
        return

    #respond to message
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
#enforce use of #bots channel
@client.before_invoke
async def common(context):
    global botsChannel
    botsChannel = discord.utils.get(context.guild.channels, name="bots")
    if (botsChannel):
        if (context.channel != botsChannel):
            await context.message.delete() #delete message  #TODO: this breaks commands that rely on reactions (bonk)
            await botsChannel.send(f'<@{context.author.id}>')
    else:
        botsChannel = context.channel

## HELP
@client.command()
async def help(context):
    embed = discord.Embed(title="What can men do against such reckless hate?", color=discord.Color.red())
    
    embed.add_field(name="!help", 
					value="❓")
    embed.add_field(name="!ping, !pong", 
					value="🏓")
    embed.add_field(name="!dance", 
					value="🎉")
    embed.add_field(name="!pick a,b,...", 
					value="❔")
    embed.add_field(name="!bonk @", 
					value="<:bonk:798539206901235773>")
    await botsChannel.send(embed=embed)

## PING, PONG
@client.command()
async def ping(context):
    await botsChannel.send('pong!')
@client.command()
async def pong(context):
    await botsChannel.send('ping!')

## PICK
@client.command()
async def pick(context, *, arg):
    args = arg.split(',')

    if (len(args) == 0):
        await botsChannel.send('Is this some kind of trick question..?')
    elif (len(args) == 1):
        await botsChannel.send("Hmm.. that's a _really_ tough one.")
        await botsChannel.send(args[0])
    else:
        await botsChannel.send(random.choice(args))

## BONK
@client.command(pass_context=True)
@has_permissions(administrator=True)
async def bonk(context, arg=None):

    if (arg == None): #no person to bonk
        try:
            await context.message.add_reaction('<:bonk:798539206901235773>')
        except:
            await context.message.add_reaction('👎')

    else:
        id = None
        try:
            id = int(arg.strip('<@!>'))
        except ValueError:
            pass #ignore this error, user will be null

        bonkRole = discord.utils.get(context.guild.roles, name='Bonk Jail')
        user = context.guild.get_member(id)

        if (user == None): #user does not exist, or is not in guild
            print('Invalid user')
            return
            
        if (bonkRole == None): #bonk role does not exist
            #TODO: create role if able
            print("Role 'Bonk Jail' does not exist")
            await context.channel.send('<:bonk:798539206901235773>')
            return
        elif (bonkRole in user.roles): #already bonked (unbonk)
            await user.remove_roles(bonkRole)
            await context.channel.send("https://tenor.com/view/gandalf-theoden-king-meduseld-two-towers-gif-22261302") #I release you
        else:
            await user.add_roles(bonkRole)
            #original channel
            await context.channel.send('<:bonk:798539206901235773>')
            if random.randint(0, 5) <= 2:
                await context.channel.send('https://www.youtube.com/watch?v=2D7P1khV40U')
            
            #bonk-jail
            bonkJail = discord.utils.get(context.guild.channels, name="bonk-jail")
            if (bonkJail == None): #bonk-jail channel does not exist
                #TODO: create channel if able
                print("'#bonk-jail' channel does not exist")
                return

            await bonkJail.send(f'<@{id}>')
            responses = ['https://c.tenor.com/TCcLhuhnNHoAAAAd/captain-america.gif', 'https://tenor.com/view/lion-king-scar-hes-not-one-ofus-leaving-gif-15363945', 'https://tenor.com/view/lion-king-deception-disgrace-gif-18508159', 'https://open.spotify.com/track/6Y4rDNttdC0T5hDImzjaSJ?si=10f2f9a58c3c4c27']
            await bonkJail.send(random.choice(responses))
            

@bonk.error
async def kick_error(error, context):
    if isinstance(error, MissingPermissions):
        try:
            await context.message.add_reaction('<:ekkydisapproves:876951860144144454>')
        except:
            await context.message.add_reaction('👎')
        await context.channel.send('https://tenor.com/view/lotr-lord-of-the-rings-theoden-king-of-rohan-you-have-no-power-here-gif-4952489')
    else:
        raise error

# MAIN
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
client.run(TOKEN)