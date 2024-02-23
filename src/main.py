import os
import random
import time
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
from dotenv import load_dotenv
from datetime import datetime, timedelta
import steamAPI
import bibleAPI
import asyncio
import re
import json

load_dotenv('token.env')


class ThisNeedsAName:

  def __init__(self, user, guild, channel, message) -> None:
    self.user = user
    self.guild = guild
    self.channel = channel
    self.message = message
    self.time = datetime.now()


# GLOBALS
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True
client = commands.Bot(intents=intents,
                      command_prefix='!',
                      help_command=None,
                      case_insensitive=True)

awake = False

botsChannel = None
deciCache = [None, None]

presenceQueue = []
reminderQueue = []

decisionEmbed = None

# MESSAGES
responses = [ # TODO store these GIFs and don't rely upon links
  ['where did you ', 'https://cdn.discordapp.com/attachments/1042840873714593843/1046228124284747928/Man_of_Steel_1080p_I_was_bred_to_be_a_warrior_Kal_Trained_my.gif'],  # zod
  ['ride', 'https://cdn.discordapp.com/attachments/901521305931747348/1046164201867051018/ride_now_ride_for_ruin_and_the_worlds_ending.gif'],  # did you say ride?
  ['lotr bad', 'https://media.tenor.com/qRXLEt2PRDYAAAAC/gandalf-keep.gif'],  # forked tongue
  [['circadian', 'sympathetic nerve', 'rem ', 'read a book'], 'https://media.tenor.com/runLaIlilAUAAAAC/gandalf-paper.gif'],  # josh reading a book
  ['deforestation', 'https://tenor.com/view/barbalbero-treebeard-lotr-lord-of-the-rings-ent-gif-17533852'],  # treebeard
  ["what'd you tell me", 'You wanna win and walk away?'],  # andor
  [['for the alliance', 'for the king', 'long live the king'], 'https://tenor.com/view/halo-halo2-halo-oorah-gif-15782884'],  # hoorah
  ['documenta', 'https://cdn.discordapp.com/attachments/901521305931747348/968570296678367272/documentary.gif'],  # Jon
  ['sea', 'https://cdn.discordapp.com/attachments/902687545857560646/1022496891658829895/download_1.gif'],  # the sea is always right
  ['rue', 'https://tenor.com/view/key-thorin-oakenshield-all-those-who-doubted-us-rue-this-day-gif-17140731'],
  ['bronner', 'https://64.media.tumblr.com/075e4cb93cabb63d7f049ad35accaa52/tumblr_myocbow0wn1rcwa0zo1_250.gif'],  # that is what they used to call me
  ['hello there', 'https://tenor.com/view/grevious-general-kenobi-star-wars-gif-11406339'],  # general kenobo
  [['heretic', 'heresy'], 'https://tenor.com/view/heretic-halo2-arbiter-grunts-gif-19621018'],
  [['traitor', 'treason'], 'https://cdn.discordapp.com/attachments/901521305931747348/901984847608811590/Heresy.gif'],  # nay, it was heresy
  ['vexor', 'https://c.tenor.com/RaG9beTFOSMAAAAC/batman-vs.gif'],  # why did you say that name?
  ['jahan', 'https://tenor.com/view/legolas-the-lord-of-rings-gif-23169554'],  # the white wizard
  ['die', 'https://64.media.tumblr.com/c3af27aefc0d51d80754d7b1158ae696/tumblr_moj2ur3xxU1qelmhao6_250.gif'],  # then I shall die as one of them
  ['weevil', 'https://cdn.discordapp.com/attachments/1042840873714593843/1047539453226401822/lesser_of_two_weevils.gif'],  # master and commander
  [' late', 'https://i.giphy.com/media/HVaHPyE3DUFW/giphy.webp'],  # a wizard is never late
  ['i wish', 'https://64.media.tumblr.com/56a1245360562846c1a04dc6dd25ff50/9b20e3deca4fcdc8-2e/s540x810/87425a55dd09fa3aa8a3cd7bb8732dede693913e.gif'],  # so do all
  ['one day', 'https://tenor.com/view/aragorn-but-notthis-day-lotr-gif-14120761'],  # but it is not this day
  [['victor', 'win', ' ftw'], 'https://64.media.tumblr.com/467b4edba8605ad6f7afe7dd5f537516/tumblr_o3gyn5GSOt1ru8yv8o2_500.gif'],  # theoden
  ['you have my ', 'https://tenor.com/view/axe-lotr-gif-5532799'],  # and my axe!
  ['sand', 'https://tenor.com/view/anakin-star-wars-padme-gif-5048790'],  # I hate sand
  [['potato', 'tater'], 'https://tenor.com/view/potato-po-tay-toes-lord-of-the-rings-lotr-samwise-gamgee-gif-5379028'],  # po-tay-toes
  ['mein', 'https://cdn.discordapp.com/attachments/1042840873714593843/1047532238562136084/ein_mein.gif'],  # they call it a mein!
  ['mine', 'https://cdn.discordapp.com/attachments/1042840873714593843/1047532220044283954/a_mine.gif'],  # they call it a mine!
  [['lift', 'elevator'], 'https://cdn.discordapp.com/attachments/1121914639811346553/1134813866820386826/MOSHED-2023-7-29-13-44-6.gif'],  # scared hamster
  ['frontflip', 'https://cdn.discordapp.com/attachments/895064046020202498/922284196871942164/ezgif-5-d8195ff3b7.gif'],  # backflip
  [['sbonc', 'sponc'], 'https://media.tenor.com/LZqN6gPJULcAAAAC/playing-squash-faisal-khan.gif'], # squash
  [['bonk bat', 'bonketh bat'], 'https://tenor.com/view/stay-down-warning-iron-man-final-warning-gif-13869294'],  # stay down. final warning
  ['flip', 'https://tenor.com/view/trex-backflip-gif-11354213'],  # flip
  ['borg', 'https://64.media.tumblr.com/614e4e4c0a1fa60eda4dff4d23e37965/87b2129a522ab83f-30/s540x810/54ec3cf0689a9f35dfa721b3bf5a2363968bb76d.gif'],  # shadowfax
  ['wrex', 'https://media0.giphy.com/media/ep3PeQAZGYG4TjHuNe/giphy.gif?cid=82a1493b3p187xacdh2ecmdzpxi65irtxz1xvtau8we3vz2z&rid=giphy.gif']  # "SHEPARD"
]
reactions = [
  # flags
  ['alliance', '<:theAlliance:899087916251353118>'],
  ['argentin', '🇦🇷'],
  [['canada', 'canhead'], '🇨🇦'],
  [['australia', 'didgeridumdum'], '🇦🇺'],
  [['new zealand', 'kiwi'], '🇳🇿'],
  [['malta', 'maltesers'], '🇲🇹'],
  [['gmt', 'bst'], '🇬🇧'],
  [['cet', 'cest'], '🇨🇭'],
  # jerry
  ['doubt', '<:doubt:922292403627491378>'],
  [['jerry', 'good bot', 'attaboi', 'attabot'], '❤️'],
  ['beans', '<:beans:796047923711836210>'],
]
summonGIFs = [
  'https://thehuffmanpost.files.wordpress.com/2019/07/ecc86735e2d3ee72317cfeb75d9d030746e87987c5610a17f604807870f763f4_1.gif?w=322&h=177',  #eomer
  'https://tenor.com/view/lord-of-the-rings-summon-fulfill-oath-pledge-gif-22388472'  # aragorn
]

perspectiveConvertor = {
  # first -> second
  'my': 'your',
  'me': 'you',
  'i': 'you',
  'mine': 'yours',
  'am': 'are',
  "i'm": "you're",
  "i'll": "you'll",
  # second -> third
  'your': 'their',
  'you': 'they',
  'yours': 'theirs',
  "you're": "they're",
  "you'll": "they'll"
}

@client.listen()
async def on_ready():

  global awake
  global reminderQueue

  print(f'Logged in as {client.user}\n')
  await client.change_presence(status=discord.Status.invisible)

  # profile
  name, avatar = getActivity()
  if (not os.environ.get('DEBUG')):
    try:
      await client.user.edit(avatar=avatar)
    except discord.errors.HTTPException:
      print('Avatar not changed: HTTPException')

  # reminders
  try:
    with open('data/dynamic/reminders.json', 'r') as file:
      reminderQueue = json.load(file)
  except FileNotFoundError:
    print('No reminders found.')
  except json.decoder.JSONDecodeError:
    print('No reminders found.')
  for reminder in reminderQueue:
    reminderTime = (float)(reminder['time'])
    if (reminderTime >= time.time()):
      asyncio.create_task(setReminder(reminder))
    else:
      reminderQueue.remove(reminder)
  with open('data/dynamic/reminders.json', 'w') as file:
    json.dump(reminderQueue, file, indent=4)

  awake = True

  print('Ready.\n')
  await client.change_presence(
    activity=discord.Activity(type=discord.ActivityType.listening, name=name))


@client.listen()
async def on_message(context):

  message = context.content.lower()  # removes case sensitivity
  if ((not awake)
      or (context.author == client.user)):  # awake only / ignore self
    return
  if (message.startswith('http')):  # ignore links (GIFs)
    return

  # SOFT COMMANDS
  ## TAG
  shouldRespond = False
  user = context.guild.get_member(getTagFromMessage(message))
  if (user is not None):

    # presence waitlist
    if (user.status.name in ('offline', 'idle')):
      presenceQueue.append(
        ThisNeedsAName(user.id, context.guild.id, context.channel, context.id))

    # tag game
    if (user.id == client.user.id):  # if self is tagged
      shouldRespond = random.randint(0, 100) < 40  # 40%

    tagRole = discord.utils.get(context.guild.roles, name='It')
    if ((tagRole is not None) and (tagRole in context.author.roles)):

      playerRole = discord.utils.get(context.guild.roles, name='PlayingTag')
      if ((playerRole is None) or (playerRole in user.roles)):

        # remove role
        await context.author.remove_roles(tagRole)

        # assign role
        if (user.id == client.user.id):  # if self is tagged
          await user.add_roles(tagRole)

          if shouldRespond:
            await context.channel.send(
              random.choice([
                'https://tenor.com/view/starwars-han-solo-tag-youre-it-stormtrooper-gif-20240479',
                'https://tenor.com/view/monty-python-holy-grail-horse-on-my-way-omw-gif-13663405',
                'https://imgur.com/VVMZWAn',
                'https://tenor.com/view/halo-master-chief-halo-infinite-xbox-xbox-series-x-gif-19586612'
              ]))
            shouldRespond = False

          time.sleep(2)
          await user.remove_roles(tagRole)

          n = context.guild.member_count - 1
          while ((playerRole not in user.roles)
              or (user.id == client.user.id)):  # no tagging non-players, or self
            user = context.guild.members[random.randint(0, n)]

          await context.channel.send(f'<@{user.id}>')
        await user.add_roles(tagRole)

  # BIBLE REFERENCES
  references = bibleAPI.getBibleReferences(message)
  if (references != None):
    for reference in references:
      await context.channel.send(reference[0])
      for chunk in reference[1]:
        await context.channel.send(f'> {chunk}')
    return

  # REMINDERS
  if ('remind' in message):
    await remind(context)
    return

  if ('jerry' in message):
    ## BONK
    if ('bonk' in message):
      if (not context.author.guild_permissions.administrator):
        await context.channel.send('https://tenor.com/view/lotr-lord-of-the-rings-theoden-king-of-rohan-you-have-no-power-here-gif-4952489')
        return
      id = getTagFromMessage(message)
      await bonk(context, f'<@{id}>')
      return

    ## SUMMON
    if ('summon' in message):
      delay = extractTime(message)

      if ('@everyone' in message):
        await summon(context, '@everyone', delay, False)
        return
      else:
        id = getTagFromMessage(message)
        if (id is not None):
          await summon(context, f'<@{id}>', delay, False)
          return
        else:
          await context.message.add_reaction('❓')

  ## DANCE
  if ('dance' in message):
    danceMoves = [
      'https://cdn.discordapp.com/attachments/901521305931747348/922290586487246888/ezgif-5-be2c8bfa47.gif',
      'https://c.tenor.com/b2Fo3D-oA20AAAAC/dinosaur-pole-dance.gif',
      'https://tenor.com/view/monty-python-and-the-holy-grail-dance-celebrate-gif-12275693',
      'https://tenor.com/view/monty-python-camelot-dance-monty-python-dance-camelot-medieval-gif-17123270',
      'https://tenor.com/view/katy-bentz-spin-spinny-dinosaur-gif-23363009',
      'https://tenor.com/view/smeagle-gollum-gif-8750815',
      'https://tenor.com/view/simba-lion-king-funny-disney-gif-5763716',
      'https://tenor.com/view/skyrim-dragon-dance-elder-scrolls-gif-6076592',
      'https://media.tenor.com/VNcLWS_jDR8AAAAC/bluey-dance.gif',
      'https://tenor.com/view/yahia-potato-dance-gif-16070760'
    ]
    await context.channel.send(random.choice(danceMoves))
    return

  # REACT
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

  # DECIDE STEAM GAME
  if ('jerry' in message and 'deci' in message):
    await decide(context)
    return

  # WORDS OF WISDOM
  if (('jerry' in message) and ('wis' in message)):
    try:
      with open('data/static/fortune.txt', 'r') as file:
        options = []
        for line in file:
          line = line.rstrip() + ' '
          if ((line != ' ') and (line[0] != '#')):
            options.append(line)

      n = random.randint(0, len(options) - 1)
      if ("{}" in options[n]):
        options[n] = options[n].format("<@" + str(context.author.id) + ">")
      await context.channel.send(options[n])
      return
    except IOError:
      print("Error: fortune.txt is blank")
    await context.channel.send("Hmm. I can't think of anything... 🤔")
    return

  # RESPOND
  for response in responses:
    if (type(response[0]) is str):  # single prompt
      if (response[0] in message):
        await context.channel.send(response[1])
        return
    else:  # multiple prompts (OR)
      for prompt in response[0]:
        if (prompt in message):
          await context.channel.send(response[1])
          return

  # REGURGITATE GITHUB WEBHOOKS
  if (context.author.id == 1132259152304029696):
    embed = context.embeds[0]

    if ((':main' in embed.title) or (':master' in embed.title)):
      repoName = embed.title.split(':')[0] + ']'
      embed.title = f'{repoName} has updated!'
      embed.color = discord.Color.green()

      try:
        channel = discord.utils.get(context.guild.channels, name="general")
      except:
        channel = context.channel

      await channel.send('@everyone', embed=embed)
      return


# REACTIONS
@client.listen()
async def on_reaction_add(reaction, user):
  if ((not awake) or (user.id == client.user.id)):  # awake only / ignore self
    return

  if (decisionEmbed is not None):
    voteCount = discord.utils.get(reaction.message.reactions,
                                  emoji=reaction.emoji).count - 1
    if ((reaction.message.id == decisionEmbed[0].id)
        and (voteCount > decisionEmbed[1] * 0.5)):

      # refresh embed with new game
      try:
        embed = getGame(deciCache[1], multiplayer=(decisionEmbed[1] > 1))

        # output result
        await decisionEmbed[0].clear_reactions()
        await decisionEmbed[0].edit(embed=embed)
        await decisionEmbed[0].add_reaction('🔄')

      except Exception as e:
        await reaction.message.channel.send("uh oh, I broke")
        print(e)


# PRESENCE
@client.event
async def on_presence_update(_, after):

  if (after.status.name in ('online', 'dnd')):

    for event in presenceQueue:
      if ((event.user == after.id) and (event.guild == after.guild.id)):

        if (datetime.now() - event.time < timedelta(minutes=1)):
          original = await event.channel.fetch_message(event.message)
          if (original is not None):
            await original.reply(
              'https://cdn.discordapp.com/attachments/901521305931747348/1174092089504583760/LOTR__The_Return_of_the_King_Pippin__sees_inside_the_Palanti.gif?ex=65665577&is=6553e077&hm=e96f9e7f58c187c8a112c58c462970dd1d2d6ceea0da4da5d767bdec707c872d&'
            )
          else:
            await event.channel.send(
              'https://cdn.discordapp.com/attachments/901521305931747348/1174092089504583760/LOTR__The_Return_of_the_King_Pippin__sees_inside_the_Palanti.gif?ex=65665577&is=6553e077&hm=e96f9e7f58c187c8a112c58c462970dd1d2d6ceea0da4da5d767bdec707c872d&'
            )

        presenceQueue.remove(event)
        break


# COMMANDS
# enforce command restrictions
@client.before_invoke
async def common(context):

  if ((not awake) and (context.command.name != 'wake')):
    raise RuntimeError  # break #TODO: find a better solution

  whitelist = ['summon', 'remind']
  for item in whitelist:
    if (item in context.message.content):
      return  # continue

  global botsChannel

  # bonk prevents commands
  bonkRole = discord.utils.get(context.guild.roles, name='Bonk Jail')
  if (bonkRole in context.author.roles):
    await context.channel.send(
      'https://tenor.com/view/lotr-lord-of-the-rings-theoden-king-of-rohan-you-have-no-power-here-gif-4952489'
    )
    raise PermissionError  #TODO: find a better solution

  # enforce use of #bots
  else:
    botsChannel = discord.utils.get(context.guild.channels, name="bots")
    if (botsChannel):
      if (context.channel != botsChannel):
        await context.message.delete(
        )  # delete message  #TODO: this breaks commands that rely on reactions (bonk)
        await botsChannel.send(f'<@{context.author.id}>')
    else:
      botsChannel = context.channel


## HELP
@client.command()
async def help(_):
  embed = discord.Embed(title="What can men do against such reckless hate?",
                        color=discord.Color.red())

  embed.add_field(name="!help", value="❓")
  embed.add_field(name="!ping, !pong", value="🏓")
  embed.add_field(name="!dance", value="🎉")
  embed.add_field(name="!pick a,b,...", value="❔")
  embed.add_field(name="!roll x", value="🎲")
  embed.add_field(name="!decide", value="<:steam:1042900928048681030>")
  embed.add_field(name="!steam <id>", value="<:steam:1044305789554266162>")
  embed.add_field(name="!bonk @", value="<:bonk:798539206901235773>")
  embed.add_field(name="!summon @", value="🎺")
  await botsChannel.send(embed=embed)


## PING, PONG
@client.command()
async def ping(_):
  await botsChannel.send('pong!')


@client.command()
async def pong(_):
  await botsChannel.send('ping!')


## PICK
@client.command()
async def pick(_, *, arg):
  args = arg.split(',')

  if (len(args) == 0):
    await botsChannel.send('Is this some kind of trick question..?')
  elif (len(args) == 1):
    await botsChannel.send("Hmm.. that's a _really_ tough one.")
    await botsChannel.send(args[0])
  else:
    await botsChannel.send(random.choice(args))


## ROLL
@client.command()
async def roll(context, arg=None):

  if (arg is None):
    await botsChannel.send(
      'https://tenor.com/view/panda-roll-over-rolling-cute-funny-animals-gif-14686316'
    )

  else:
    try:
      die = (int)(arg)
      result = random.randint(1, die)
    except ValueError:
      await context.message.add_reaction(
        '<:ekkydisapproves:876951860144144454>')
      return

    await botsChannel.send(result)


## BONK
@client.command(pass_context=True)
@has_permissions(administrator=True)
async def bonk(context, arg=None):

  if (arg is None):  # no person to bonk
    try:
      await context.message.add_reaction('<:bonk:798539206901235773>')
    except discord.errors.HTTPException:
      await context.message.add_reaction('👎🏿')

  else:
    id = None
    try:
      id = int(arg.strip('<@!>'))
    except ValueError:
      pass  # ignore this error, user will be null

    bonkRole = discord.utils.get(context.guild.roles, name='Bonk Jail')
    user = context.guild.get_member(id)

    if (user is None):  # user does not exist, or is not in guild
      print('Invalid user')
      return

    if (bonkRole is None):  # bonk role does not exist
      #TODO: create role if able
      print("Role 'Bonk Jail' does not exist")
      await context.channel.send(
        random.choice([
          '<:bonk:798539206901235773>',
          'https://tenor.com/view/ultimate-bonk-bonk-doggo-gif-26224096',
          'https://tenor.com/view/guillotine-bonk-revolution-gif-20305805',
          'https://tenor.com/view/bonk-gif-19410756'
        ]))
    elif (bonkRole in user.roles):  # already bonked (unbonk)
      await user.remove_roles(bonkRole)
      await context.channel.send(
        "https://tenor.com/view/gandalf-theoden-king-meduseld-two-towers-gif-22261302"
      )  # I release you
      return
    else:
      await user.add_roles(bonkRole)
      # original channel
      await context.channel.send(
        random.choice([
          '<:bonk:798539206901235773>',
          'https://tenor.com/view/ultimate-bonk-bonk-doggo-gif-26224096',
          'https://tenor.com/view/guillotine-bonk-revolution-gif-20305805',
          'https://tenor.com/view/bonk-gif-19410756'
        ]))
      if (random.randint(0, 5) <= 2):
        await context.channel.send(
          'https://www.youtube.com/watch?v=2D7P1khV40U')

      # bonk-jail
      bonkJail = discord.utils.get(context.guild.channels, name="bonk-jail")
      if (bonkJail is None):  # bonk-jail channel does not exist
        #TODO: create channel if (able
        print("'#bonk-jail' channel does not exist")
        return

      await bonkJail.send(f'<@{id}>')
      await bonkJail.send(
        random.choice([
          'https://c.tenor.com/TCcLhuhnNHoAAAAd/captain-america.gif',
          'https://tenor.com/view/lion-king-scar-hes-not-one-ofus-leaving-gif-15363945',
          'https://tenor.com/view/lion-king-deception-disgrace-gif-18508159',
          'https://open.spotify.com/track/6Y4rDNttdC0T5hDImzjaSJ?si=10f2f9a58c3c4c27'
        ]))
    return


@bonk.error
async def bonk_error(error, context):
  if (isinstance(error, MissingPermissions)):
    try:
      await context.message.add_reaction('<:bonk:798539206901235773>')
    except discord.errors.HTTPException:
      await context.message.add_reaction('👎🏿')
    await context.channel.send(
      'https://tenor.com/view/lotr-lord-of-the-rings-theoden-king-of-rohan-you-have-no-power-here-gif-4952489'
    )
  else:
    raise error


## DECIDE
@client.command(pass_context=True)
async def decide(context):
  global decisionEmbed

  # get users in vc
  activeUsers = []
  if (context.author.voice is None):
    print('no vc')
    await context.channel.send("You're not in a voice channel")
    return

  vc = context.author.voice.channel
  for user in vc.members:
    activeUsers.append(str(user.id))

  # get steam ids from list
  with open('data/dynamic/steamIDs.txt', 'r') as file:
    users = []
    for line in file:
      data = line[0:36].split(':')
      if (data[0] in activeUsers):
        users.append(data[1])

  if (users == []):
    print('no steam valid users')
    await context.channel.send(
      'No valid Steam users found. Use `!steam <your_steam_id>` to resolve this.'
    )
    return

  # get shared game library
  games = []
  if (users == deciCache[0]):
    games = deciCache[1].copy()
  else:
    games = steamAPI.getSharedLibrary(users)
    deciCache[0] = users.copy()
    deciCache[1] = games.copy()

  # select game
  if (deciCache[1] == [None]):
    print('no steam valid users')
    await context.channel.send(
      'No valid Steam users found. Use `!steam <your_steam_id>` to resolve this.'
    )
  elif (deciCache[1] == []):
    print('no shared games')
    await context.channel.send("You don't have any games in common.")
  else:
    try:
      embed = getGame(games, multiplayer=(len(users) > 1))

      # passive aggressive
      # boatBois = ["Don't Starve Together", "The Elder Scrolls Online", "Barotrauma"]
      # if (('524255350182903838' not in users) and (game in boatBois)):
      #     game += r' \*cough* <@!524255350182903838> \*cough*'

      # output result
      if (decisionEmbed is not None):
        await decisionEmbed[0].clear_reactions()

      decisionEmbed = (await context.channel.send(embed=embed), len(users))
      await decisionEmbed[0].add_reaction('🔄')

    except Exception as e:
      await context.channel.send("uh oh, I broke")
      print(e)


## REMIND
@client.command(pass_context=True)
async def remind(context, arg=None):

  delay = 0

  # get message
  content = context.content + ' '
  target = re.search(r'remind (me|.*?)[ .]', content)

  if (target is not None):
    target = target.group(1)
    if (target in ['me', None]):
      target = context.author.mention

    message = re.search(r'remind (me|.*?) .*?(?:to|that|about|of) (.*)', content)
    if (message is not None):
      temp = message.group(2).split(' ')

      message = f'{target}, '
      for word in temp:
        newWord = perspectiveConvertor.get(word.lower())
        if (newWord is not None):
          message += newWord + ' '
          continue
        message += word + ' '

    else:
      message = f'{target}'

  else:
    return

  # calculate delay
  timeToRemind = extractTime(context.content)

  #store to be resumable
  reminderQueue.append({
    'contents': message,
    'time': (str)(timeToRemind),
    'channel': context.channel.id,
    'message': context.id,
    'author': context.author.id
  })
  with open('data/dynamic/reminders.json', 'w') as file:
    json.dump(reminderQueue, file, indent=4)

  asyncio.create_task(setReminder(reminderQueue[-1]))
  await context.add_reaction('👍🏿')


## STEAM
@client.command(pass_context=True)
async def steam(context, arg=None):
  if (arg is None):  # no person to bonk
    try:
      await context.message.add_reaction('<:bonk:798539206901235773>')
    except discord.errors.HTTPException:
      await context.message.add_reaction('👎🏿')
  else:
    # validate keys using API
    username = steamAPI.isValidUser(arg)
    if (not username):
      await botsChannel.send(f'`{arg}` is not a valid Steam ID')
      return

    # store id in steamIDs.txt
    lines = []
    user = str(context.author.id)
    flag = False

    try:
      with open('data/dynamic/steamIDs.txt', 'r') as file:
        for line in file:
          data = line.split(':')
          if (data[0] == user):
            lines.append(f'{user}:{arg}\t#{username}\n')
            flag = True
          else:
            lines.append(line)

    except FileNotFoundError:
      print("'steamIDs.txt' does not exist")

    if (flag):
      with open('data/dynamic/steamIDs.txt', 'w+') as file:
        for line in lines:
          file.write(line)
    else:
      with open('data/dynamic/steamIDs.txt', 'a') as file:
        file.write('\n' + user + ':' + arg)

    await context.message.add_reaction('👍🏿')
    await botsChannel.send(
      f'<@{context.author.id}> linked to <:steam:1044305789554266162>{username}'
    )


## LEADERBOARD
@client.command()
async def l(_):
  await botsChannel.send(
    'Sorry, I forgot to pack the leaderboard when I moved out of my place at Amazon.. so `!l` no longer functions.'
  )


## SUMMON
@client.command(pass_context=True)
async def summon(context, target=None, timeToRemind=0, subtle=True):

  if (target is None):  # no person to summon
    try:
      await context.message.add_reaction('<:bonk:798539206901235773>')
    except discord.errors.HTTPException:
      await context.message.add_reaction('👎🏿')

  elif (('<@' in target) or (target == '@everyone')):
    if (subtle):
      try:
        await context.message.delete()  # not subtle
      except discord.errors.HTTPException:
        pass

    #store to be resumable
    reminderQueue.append({
      'contents': [target, random.choice(summonGIFs)],
      'time': (str)(timeToRemind),
      'channel': context.channel.id,
      'message': context.id,
      'author': context.author.id
    })
    with open('data/dynamic/reminders.json', 'w') as file:
      json.dump(reminderQueue, file, indent=4)

    asyncio.create_task(setReminder(reminderQueue[-1]))
    await context.add_reaction('👍🏿')

  else:
    await context.message.add_reaction('❓')


## SLEEP
@client.command(pass_context=True)
async def sleep(context):
  global awake

  if (context.author.id == 220431264451264512):
    await client.change_presence(status=discord.Status.idle)
    await context.message.add_reaction('💤')
    awake = False


## WAKE
@client.command(pass_context=True)
async def wake(context):
  global awake

  if ((not awake) and (context.author.id == 220431264451264512)):
    name, _ = getActivity()

    await client.change_presence(status=discord.Status.online,
                                 activity=discord.Activity(
                                   type=discord.ActivityType.listening,
                                   name=name))
    await context.message.add_reaction('👀')
    awake = True
  else:
    await context.message.add_reaction('<:bonk:798539206901235773>')


# GENERAL FUNCTIONS
# common processes shared among features
def getTagFromMessage(message):
  keynote = None
  if ('<@!' in str(message)):
    keynote = '!'
  elif ('<@' in str(message)):
    keynote = '@'

  if (keynote is not None):

    # get target id
    msg = str(message)
    temp = ''
    flag = False
    for char in msg:
      if (char == keynote):
        flag = True
        continue
      if (flag):
        if (char == '>'):
          break
        temp += char
    try:
      temp = int(temp)
    except ValueError:
      return None

    return temp
  return None


def getActivity():
  name = "Baba Yetu"

  today = datetime.now()
  if (today.month == 12):  # CHRISTMAS
    with open('data/static/pfp/jerry-festag.png', 'rb') as image:
      avatar = image.read()

    if (today.day <= 14):  # JINGLE JAM
      name = "Jingle Jam"
    else:
      christmasSongs = [
        'Fairytale of New York', 'Jingle Bells', 'Last Christmas',
        'Feliz Navidad', 'The Little Drummer Boy', 'White Christmas',
        'Mariah Carey'
      ]
      name = random.choice(christmasSongs)

  elif ((today.month == 5) and (today.day == 4)):  # MAY THE 4TH
    name = "Duel of the Fates"

  else:
    with open('data/static/pfp/jerry.png', 'rb') as image:
      avatar = image.read()

  return name, avatar


def getGame(gamesList, multiplayer):
  game = steamAPI.getGame(
    gamesList,
    multiplayer=multiplayer)  # game must be multi-player if multiple users

  # generate embed
  embed = discord.Embed(title=game['name'],
                        color=discord.Color.dark_blue(),
                        description=game['short_description'])
  embed.url = f'https://store.steampowered.com/app/{game["steam_appid"]}'
  embed.set_thumbnail(url=game['header_image'])

  if (multiplayer):
    embed.add_field(name="Multiplayer ✅", value='')
    embed.add_field(name="Cooperative ❓", value='')
  embed.add_field(name="Controller Support ❓", value='')

  return embed


def extractTime(content):

  delay = 0

  for unit in [('day', 86400), ('hour', 3600), ('min', 60), ('sec', 1)]:
    temp = re.search(fr'(\d+|an?) {unit[0]}', content)

    if (temp is not None):
      temp = temp.group(1)

      if (temp[0] == 'a'):
        delay += unit[1]
      else:
        delay += int(temp) * unit[1]

  return time.time() + delay


async def setReminder(reminder):
  delay = (float)(reminder['time']) - time.time()

  # wait
  if (delay > 0):
    print(f'Message scheduled for {(int)(delay)}s')
    await asyncio.sleep(delay)

  channel = client.get_partial_messageable(reminder['channel'])
  context = channel.get_partial_message(reminder['message'])

  message = reminder['contents']
  if (isinstance(message, list)):

    try:
      await context.reply(message[0])
    except discord.errors.HTTPException:  # handle if message has been deleted
      await channel.send(message[0])

    for item in message[1:]:
      await channel.send(item)

  else:
    try:
      await context.reply(message)
    except discord.errors.HTTPException:  # handle if message has been deleted
      await channel.send(message)

  # update queue
  reminderQueue.remove(reminder)
  with open('data/dynamic/reminders.json', 'w') as file:
    json.dump(reminderQueue, file, indent=4)


# MAIN ---
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
client.run(TOKEN)
