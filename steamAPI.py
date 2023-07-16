import os
import random
import requests
from dotenv import load_dotenv

load_dotenv('token.env')
key = os.environ.get('STEAM_API_KEY')


def GET(endpoint):
    response = requests.get(endpoint)
    if not response:
        print('Error: ' + str(response.status_code))

    if (response.status_code == 429): # too many requests
        raise Exception("429")

    return response


def getSharedLibrary(users):
    # GET LIST OF SHARED GAMES AMONG USERS

    games = [None]
    for user in users:
        #  GET
        ## Profile Status
        response = GET('https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key='+key+'&steamids='+user+'&format=json')
        if (response.status_code == 404): # not found
            continue

        result = response.json()

        if (len(result['response']['players']) == 0):
            print(f'user ({user}) not found')
            continue
        if (result['response']['players'][0]['communityvisibilitystate'] < 3):
            print(result['response']['players'][0]['personaname'] + 'is not public')
            continue

        ## Games
        response = GET('https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key='+key+'&steamid='+user+'&format=json')
        if (response.status_code == 404): # not found
            continue

        result = response.json()

        temp = []
        if (games == [None]): # first sweep
            for game in result['response']['games']:
                temp.append(game['appid'])

        else:
            for game in result['response']['games']:
                if (game['appid'] in games):
                    temp.append(game['appid'])
            if (games == []):
                break

        games = temp.copy()

    return games


def getGame(games, multiplayer):
    # SELECT GAME FROM LIST

    while (True):
        id = random.choice(games)
        print(id)

        ## App Data
        response = GET('https://store.steampowered.com/api/appdetails?appids='+str(id))
        if (response.status_code == 404): # not found
            continue

        result = response.json()

        try:
            if (not result[str(id)]['success']):
                raise Exception("Request unsuccessful")
        except:
            print('Error')
            return None

        # ensure game is multiplayer
        for category in result[str(id)]['data']['categories']:
            if (category['description'].lower() == 'multi-player'):
                multiplayer = False
                break

        if (not multiplayer): # requirements is solo, or multi has been found
            break

        games.remove(id)
        if (games == []): # no shared multiplayer games
            print('null')
            return None

    # print(result[str(id)]['data'])
    return result[str(id)]['data']


def isValidUser(id):
    response = GET('https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key='+key+'&steamids='+id+'&format=json')
    if (response.status_code != 200):
        return False

    result = response.json()
    if (len(result['response']['players']) <= 0):
        return False

    return result['response']['players'][0]['personaname']
