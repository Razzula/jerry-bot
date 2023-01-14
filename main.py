import os, random, time
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
from dotenv import load_dotenv
from datetime import datetime, timedelta
import steamAPI

load_dotenv('token.env')

class ThisNeedsAName:
    def __init__(self, user, guild, channel) -> None:
        self.user = user
        self.guild = guild
        self.channel = channel
        self.time = datetime.now()

# GLOBALS
intents = discord.Intents.default()
intents.members = True
intents.presences = True
client = commands.Bot(intents=intents, command_prefix='!', help_command=None, case_insensitive=True)

botsChannel = None
deciCache  = [None, None]

waiting = []

@client.listen()
async def on_ready():
    print('Logged in as {0.user}\n'.format(client))


    today = datetime.now()
    if (today.month == 12): #CHRISTMAS
        with open('pfp/jerry-festag.png', 'rb') as image:
            await client.user.edit(avatar=image.read())

        if (today.day <= 14): #JINGLE JAM
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Jingle Jam"))
        else:
            christmasSongs = ['Fairytale of New York','Jingle Bells','Last Christmas','Feliz Navidad','The Little Drummer Boy','White Christmas','Mariah Carey']
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=random.choice(christmasSongs)))

    elif ((today.month == 5) and (today.day == 4)): #MAY THE 4TH
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Baba Yetu"))
        
    else:
        with open('pfp/jerry.png', 'rb') as image:
            await client.user.edit(avatar=image.read())

        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Baba Yetu"))

# MESSAGES
responses = [
    ['where did you ', 'https://cdn.discordapp.com/attachments/1042840873714593843/1046228124284747928/Man_of_Steel_1080p_I_was_bred_to_be_a_warrior_Kal_Trained_my.gif'],    #zod
    ['ride', 'https://cdn.discordapp.com/attachments/901521305931747348/1046164201867051018/ride_now_ride_for_ruin_and_the_worlds_ending.gif'], #did you say ride?
    ['lotr bad', 'https://media.tenor.com/qRXLEt2PRDYAAAAC/gandalf-keep.gif'],                                                  #forked tongue
    [['circadian', 'sympathetic nerve', 'rem ', 'read a book'], 'https://media.tenor.com/runLaIlilAUAAAAC/gandalf-paper.gif'],   #josh reading a book
    ['deforestation', 'https://tenor.com/view/barbalbero-treebeard-lotr-lord-of-the-rings-ent-gif-17533852'],                   #treebeard
    ["what'd you tell me", 'You wanna win and walk away?'],                                                                     #andor
    [['for the alliance', 'for the king'], 'https://tenor.com/view/halo-halo2-halo-oorah-gif-15782884'],                        #hoorah
    ['documenta', 'https://cdn.discordapp.com/attachments/901521305931747348/968570296678367272/documentary.gif'],              #Jon
    ['sea', 'https://cdn.discordapp.com/attachments/902687545857560646/1022496891658829895/download_1.gif'],                    #the sea is always right
    ['rue', 'https://tenor.com/view/key-thorin-oakenshield-all-those-who-doubted-us-rue-this-day-gif-17140731'],
    ['bronner', 'https://64.media.tumblr.com/075e4cb93cabb63d7f049ad35accaa52/tumblr_myocbow0wn1rcwa0zo1_250.gif'],             #that is what they used to call me
    ['hello there', 'https://tenor.com/view/grevious-general-kenobi-star-wars-gif-11406339'],                                   #general kenobo
    [['heretic','heresy'], 'https://tenor.com/view/heretic-halo2-arbiter-grunts-gif-19621018'],
    [['traitor', 'treason'], 'https://cdn.discordapp.com/attachments/901521305931747348/901984847608811590/Heresy.gif'],        #nay, it was heresy
    ['vexor', 'https://c.tenor.com/RaG9beTFOSMAAAAC/batman-vs.gif'],                                                            #why did you say that name?
    ['jahan', 'https://tenor.com/view/legolas-the-lord-of-rings-gif-23169554'],                                                 #the white wizard
    ['die', 'https://64.media.tumblr.com/c3af27aefc0d51d80754d7b1158ae696/tumblr_moj2ur3xxU1qelmhao6_250.gif'],                 #then I shall die as one of them
    ['weevil', 'https://cdn.discordapp.com/attachments/1042840873714593843/1047539453226401822/lesser_of_two_weevils.gif'],     #master and commander
    [' late', 'https://i.giphy.com/media/HVaHPyE3DUFW/giphy.webp'],                                                             #a wizard is never late
    ['i wish', 'https://64.media.tumblr.com/56a1245360562846c1a04dc6dd25ff50/9b20e3deca4fcdc8-2e/s540x810/87425a55dd09fa3aa8a3cd7bb8732dede693913e.gif'], #so do all
    ['one day', 'https://tenor.com/view/aragorn-but-notthis-day-lotr-gif-14120761'],                                                #but it is not this day
    [['victor', 'win', ' ftw'], 'https://64.media.tumblr.com/467b4edba8605ad6f7afe7dd5f537516/tumblr_o3gyn5GSOt1ru8yv8o2_500.gif'],  #theoden
    ['you have my ', 'https://tenor.com/view/axe-lotr-gif-5532799'],                                                                #and my axe!
    ['sand', 'https://tenor.com/view/anakin-star-wars-padme-gif-5048790'],                                                      #I hate sand
    [['potato', 'tater'], 'https://tenor.com/view/potato-po-tay-toes-lord-of-the-rings-lotr-samwise-gamgee-gif-5379028'],       #po-tay-toes
    ['mein', 'https://cdn.discordapp.com/attachments/1042840873714593843/1047532238562136084/ein_mein.gif'],                    #they call it a mein!
    ['mine', 'https://cdn.discordapp.com/attachments/1042840873714593843/1047532220044283954/a_mine.gif'],                      #they call it a mine!
    [['lift', 'elevator'], 'https://tenor.com/view/see-it-like-final-hamster-scared-gif-14498643'],                             #scared hamster
    ['frontflip', 'https://cdn.discordapp.com/attachments/895064046020202498/922284196871942164/ezgif-5-d8195ff3b7.gif'],       #backflip
    ['flip', 'https://tenor.com/view/trex-backflip-gif-11354213'],                                                              #flip
    ['wrex', 'https://media0.giphy.com/media/ep3PeQAZGYG4TjHuNe/giphy.gif?cid=82a1493b3p187xacdh2ecmdzpxi65irtxz1xvtau8we3vz2z&rid=giphy.gif'] #"SHEPARD"
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
    if (context.author == client.user): #ignore self
        return
    if (message.startswith('http')): #ignore links (GIFs)
        return

    ##TAG
    shouldRespond = False
    user = context.guild.get_member(getTagFromMessage(message))
    if (user != None):

        #presence waitlist
        if (user.status.name == 'offline' or user.status.name == 'idle'):
            waiting.append(ThisNeedsAName(user.id, context.guild.id, context.channel))

        #tag game
        if (user.id == client.user.id): #if self is tagged
            if (random.randint(0, 100) < 40): #40%
                shouldRespond = True
            else:
                shouldRespond= False

        tagRole = discord.utils.get(context.guild.roles, name='It')
        if ((tagRole != None) and (tagRole in context.author.roles)):
            
            playerRole = discord.utils.get(context.guild.roles, name='PlayingTag')
            if ((playerRole == None) or (playerRole in user.roles)):
                
                #remove role
                await context.author.remove_roles(tagRole)

                #assign role
                if (user.id == client.user.id): #if self is tagged
                    await user.add_roles(tagRole)

                    if shouldRespond:
                        await context.channel.send(random.choice(['https://tenor.com/view/starwars-han-solo-tag-youre-it-stormtrooper-gif-20240479', 'https://tenor.com/view/monty-python-holy-grail-horse-on-my-way-omw-gif-13663405', 'https://imgur.com/VVMZWAn', 'https://tenor.com/view/halo-master-chief-halo-infinite-xbox-xbox-series-x-gif-19586612']))
                        shouldRespond = False

                    time.sleep(2)
                    await user.remove_roles(tagRole)

                    n = context.guild.member_count - 1
                    while ((playerRole not in user.roles) or (user.id == client.user.id)): #no tagging non-players, or self
                        user = context.guild.members[random.randint(0, n)]

                    await context.channel.send(f'<@{user.id}>')
                await user.add_roles(tagRole)

    ##BONK
    if ('jerry' in message and 'bonk' in message):
        id = getTagFromMessage(message)
        await bonk(context, f'<@{id}>')

    ##BONK
    if ('jerry' in message and 'summon' in message):
        if ('@everyone' in message):
            await summon(context, '@everyone')
        else:
            id = getTagFromMessage(message)
            await summon(context, f'<@{id}>')

    ##DANCE
    if ('dance' in message):
        danceMoves = ['https://cdn.discordapp.com/attachments/901521305931747348/922290586487246888/ezgif-5-be2c8bfa47.gif', 'https://c.tenor.com/b2Fo3D-oA20AAAAC/dinosaur-pole-dance.gif', 'https://tenor.com/view/monty-python-and-the-holy-grail-dance-celebrate-gif-12275693', 'https://tenor.com/view/monty-python-camelot-dance-monty-python-dance-camelot-medieval-gif-17123270', 'https://tenor.com/view/katy-bentz-spin-spinny-dinosaur-gif-23363009', 'https://tenor.com/view/smeagle-gollum-gif-8750815', 'https://tenor.com/view/simba-lion-king-funny-disney-gif-5763716', 'https://tenor.com/view/skyrim-dragon-dance-elder-scrolls-gif-6076592', 'https://media.tenor.com/VNcLWS_jDR8AAAAC/bluey-dance.gif']
        await context.channel.send(random.choice(danceMoves))
        return

    ##REACT
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

    ##DECIDE STEAM GAME
    if ('jerry' in message and 'deci' in message):
        await decide(context)
        return

    ##WORDS OF WISDOM
    if (('jerry' in message) and ('wis' in message)):
        try:
            file = open('fortune.txt', 'r')
            options = []
            for line in file:
                line = line.rstrip() + ' '
                if ((line != ' ') and (line[0] != '#')):
                    options.append(line)

            l = len(options) - 1
            n = random.randint(0, l)
            if ("{}" in options[n]):
                options[n] = options[n].format("<@" + str(context.author.id) + ">")
            await context.channel.send(options[n])
            return
        except IOError:
            print("Error: fortune.txt is blank")
        await context.channel.send("Hmm. I can't think of anything... 🤔")
        return

    ##RESPOND
    for response in responses:
        if (type(response[0]) is str): #single prompt
            if (response[0] in message):
                await context.channel.send(response[1])
                return
        else: #multiple prompts (OR)
            for prompt in response[0]:
                if (prompt in message):
                    await context.channel.send(response[1])
                    return
            
# REACTIONS
@client.listen()
async def on_reaction_add(reaction, user):
    if (user == client.user): #ignore self
        return

# PRESENCE
@client.event
async def on_member_update(before, after):

    if (after.status.name == 'online' or after.status.name == 'dnd'):

        for event in waiting:
            if (event.user == after.id and event.guild == after.guild.id):

                if (datetime.now() - event.time < timedelta(minutes=1)):
                    await event.channel.send('https://thumbs.gfycat.com/BogusAppropriateBird-size_restricted.gif')

                waiting.remove(event)
                break

# COMMANDS
#enforce command restrictions
@client.before_invoke
async def common(context):

    whitelist = ['summon']
    for item in whitelist:
        if (item in context.message.content):
            return

    global botsChannel

    #bonk prevents commands
    bonkRole = discord.utils.get(context.guild.roles, name='Bonk Jail')
    if (bonkRole in context.author.roles):
        await context.channel.send('https://tenor.com/view/lotr-lord-of-the-rings-theoden-king-of-rohan-you-have-no-power-here-gif-4952489')
        raise PermissionError #TODO: find a better solution

    #enforce use of #bots
    else:
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
    embed.add_field(name="!decide", 
					value="<:steam:1042900928048681030>")
    embed.add_field(name="!steam <id>", 
					value="<:steam:1044305789554266162>")
    embed.add_field(name="!bonk @", 
					value="<:bonk:798539206901235773>")
    embed.add_field(name="!summon @", 
					value="🎺")
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
            #TODO: create role if (able
            print("Role 'Bonk Jail' does not exist")
            await context.channel.send('<:bonk:798539206901235773>')
        elif (bonkRole in user.roles): #already bonked (unbonk)
            await user.remove_roles(bonkRole)
            await context.channel.send("https://tenor.com/view/gandalf-theoden-king-meduseld-two-towers-gif-22261302") #I release you
        else:
            await user.add_roles(bonkRole)
            #original channel
            await context.channel.send('<:bonk:798539206901235773>')
            if (random.randint(0, 5) <= 2):
                await context.channel.send('https://www.youtube.com/watch?v=2D7P1khV40U')
            
            #bonk-jail
            bonkJail = discord.utils.get(context.guild.channels, name="bonk-jail")
            if (bonkJail == None): #bonk-jail channel does not exist
                #TODO: create channel if (able
                print("'#bonk-jail' channel does not exist")
                return

            await bonkJail.send(f'<@{id}>')
            await bonkJail.send(random.choice(['https://c.tenor.com/TCcLhuhnNHoAAAAd/captain-america.gif', 'https://tenor.com/view/lion-king-scar-hes-not-one-ofus-leaving-gif-15363945', 'https://tenor.com/view/lion-king-deception-disgrace-gif-18508159', 'https://open.spotify.com/track/6Y4rDNttdC0T5hDImzjaSJ?si=10f2f9a58c3c4c27']))
        return
            

@bonk.error
async def kick_error(error, context):
    if (isinstance(error, MissingPermissions)):
        try:
            await context.message.add_reaction('<:ekkydisapproves:876951860144144454>')
        except:
            await context.message.add_reaction('👎')
        await context.channel.send('https://tenor.com/view/lotr-lord-of-the-rings-theoden-king-of-rohan-you-have-no-power-here-gif-4952489')
    else:
        raise error

## DECIDE
@client.command(pass_context=True)
async def decide(context):
    global deciCache

    #get users in vc
    activeUsers = []
    if (context.author.voice == None):
        print('no vc')
        await context.channel.send("You're not in a voice channel")
        return
    
    vc = context.author.voice.channel
    for user in vc.members:
        activeUsers.append(str(user.id))

    #get steam ids from list
    file = open('steamIDs.txt', 'r')
    users = []
    for line in file:
        data = line[0:36].split(':')
        if (data[0] in activeUsers):
            users.append(data[1])

    if (users == []):
        print('no steam valid users')
        await context.channel.send('No valid Steam users found. Use `!steam <your_steam_id>` to resolve this.')
        return

    #get shared game library
    games = []
    if (users == deciCache[0]):
        games = deciCache[1].copy()
    else:
        games = steamAPI.getSharedLibrary(users)
        deciCache[0] = users.copy()
        deciCache[1] = games.copy()

    #select game
    if (deciCache[1] == [None]):
        print('no steam valid users')
        await context.channel.send('No valid Steam users found. Use `!steam <your_steam_id>` to resolve this.')
    elif (deciCache[1] == []):
        print('no shared games')
        await context.channel.send("You don't have any games in common.")
    else:
        try:
            game = steamAPI.getGame(games, multiplayer=(len(users) > 1)) #game must be multi-player if multiple users

            #passive aggressive
            boatBois = ["Don't Starve Together","The Elder Scrolls Online","Barotrauma"]
            if (('524255350182903838' not in users) and (game in boatBois)):
                game += ' \*cough* <@!524255350182903838> \*cough*'

            #output result
            await context.channel.send(game)
        except:
            await context.channel.send("uh oh, I broke")

## STEAM
@client.command(pass_context=True)
async def steam(context, arg=None):
    if (arg == None): #no person to bonk
        try:
            await context.message.add_reaction('<:bonk:798539206901235773>')
        except:
            await context.message.add_reaction('👎')
    else:
        #validate keys using API
        username = steamAPI.isValidUser(arg)
        if (not username):
            await botsChannel.send(f'`{arg}` is not a valid Steam ID')
            return

        #store id in steamIDs.txt
        lines = []
        user = str(context.author.id)
        flag = False
        try:
            file = open('steamIDs.txt', 'r')
        except:
            print("'steamIDs.txt' does not exist")
        else:
            for line in file:
                data = line.split(':')
                if (data[0] == user):
                    lines.append(f'{user}:{arg}\t#{username}\n')
                    flag = True
                else:
                    lines.append(line)
            file.close()

        if (flag):
            file = open('steamIDs.txt', 'w+')
            for line in lines:
                file.write(line)
        else:
            file = open('steamIDs.txt', 'a')
            file.write('\n' + user + ':' + arg)
        file.close()

        
        await context.message.add_reaction('👍')
        await botsChannel.send(f'<@{context.author.id}> linked to <:steam:1044305789554266162>{username}')

##LEADERBOARD
@client.command()
async def l(context):
    await botsChannel.send('Sorry, I forgot to pack the leaderboard when I moved out of my place at Amazon.. so `!l` no longer functions.')

##SUMMON
@client.command(pass_context=True)
async def summon(context, arg=None):

    if (arg == None): #no person to bonk
        try:
            await context.message.add_reaction('<:bonk:798539206901235773>')
        except:
            await context.message.add_reaction('👎')

    elif (('<@' in arg) or (arg == '@everyone')):
        try:
            await context.message.delete() #! not subtle
        except:
            pass

        await context.channel.send(arg)
        await context.channel.send(random.choice(['https://thehuffmanpost.files.wordpress.com/2019/07/ecc86735e2d3ee72317cfeb75d9d030746e87987c5610a17f604807870f763f4_1.gif?w=322&h=177', 'https://tenor.com/view/lord-of-the-rings-summon-fulfill-oath-pledge-gif-22388472'])) #eomer, aragorn
    else:
        await context.message.add_reaction('❓')

# GENERAL FUNCTIONS
# common processes shared among features
def getTagFromMessage(message):
    keynote = None
    if ('<@!' in str(message)):
        keynote = '!'
    elif ('<@' in str(message)):
        keynote = '@'

    if (keynote != None):

        #get target id
        msg = str(message)
        temp = ''
        flag = False
        for i in range(len(msg)):
            if (msg[i] == keynote):
                flag = True
                continue
            if (flag):
                if (msg[i] == '>'):
                    break
                else:
                    temp += msg[i]
        try:
            temp = int(temp)
        except:
            return None

        return temp
    return None

# MAIN ---
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
client.run(TOKEN)