# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ
'''An interface to the Steam API for retrieving TODO.'''
import os
import random
from enum import Enum
from typing import Any
import requests

class SteamAPI:
    """TODO"""

    class States(Enum):
        """TODO"""
        INVALID = 404
        PRIVATE = 401

    def __init__(self, apiKey: str):
        self.API_KEY = apiKey

    def get(self, endpoint):
        """GET request to the Steam API."""

        response = requests.get(endpoint, timeout=15)
        if (not response):
            print('Error: ' + str(response.status_code)) # TODO: log error

        if (response.status_code == 429):  # too many requests
            raise requests.exceptions.TooManyRedirects()

        return response

    def getSharedLibrary(self, users: list[tuple[str, str]]):
        """Get list of shared games among users."""

        invalidUsers: list[tuple[str, self.States]] = []
        sharedLibrary: list[str | None] = [None] # we need to know if this is the first iteration

        # GET Profile Status
        response = self.get(
            'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key='
            + self.API_KEY
            + '&steamids='
            + ','.join([user[1] for user in users]) # list of steamIDs
            + '&format=json'
        )
        if (response.status_code == 404):
            # not found; error in url
            return (None, None)

        steamUsers = response.json().get('response').get('players')

        # process returned Steam users
        steamIDs: list[str] = []
        for user in users:
            validUser = False

            for steamUser in steamUsers:
                if (steamUser.get('steamid') == user[1]): # match

                    if (steamUser.get('communityvisibilitystate') < 3):
                        # user is not public, ergo we cannot access their games
                        invalidUsers.append((user[0], self.States.PRIVATE))
                    else:
                        steamIDs.append(steamUser.get('steamid'))
                        validUser = True
                    break

            if (not validUser):
                # user not found
                invalidUsers.append((user[0], self.States.INVALID))

        # GET Games
        for steamID in steamIDs: # unfortunately, we need to make a request for each user
            response = self.get(
                'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key='
                + self.API_KEY
                + '&steamid='
                + steamID
                + '&format=json'
            )
            if (response.status_code == 404):
                # not found; error in url
                return (None, None)

            result = response.json().get('response').get('games')
                # interestibgly, we can also see some statistics here, such as:
                # - playtime
                # - last played
            library = [game.get('appid') for game in result]

            if (sharedLibrary == [None]):
                # first sweep, no need for comparison
                sharedLibrary = library
            else:
                # we need to union the existing list with the new result
                sharedLibrary = list(set(sharedLibrary) | set(library))

        return (sharedLibrary, invalidUsers)

    def selectGame(self, gamesList: list[str], requireMultiplayer: bool) -> dict[str, Any] | None:
        """Select a game from the list."""

        localGamesList = gamesList.copy()

        result: dict[str, Any] = {}
        isMultiplayer = False

        while (len(localGamesList) > 0):

            # select random game
            appID = random.choice(gamesList)

            # GET App Data
            response = self.get(
                f'https://store.steampowered.com/api/appdetails?appids={appID}'
            )
            if (response.status_code == 404):
                # not found; error with ID
                localGamesList.remove(appID)
                continue

            result = response.json().get(str(appID)).get('data')

            if (not requireMultiplayer):
                break

            # ensure game is multiplayer
            if ((categories := result.get('categories')) is not None):
                for category in categories:
                    if (category.get('description').lower() == "multi-player"):
                        isMultiplayer = True
                        break

            if (isMultiplayer):
                break

            localGamesList.remove(appID)

        return result # TODO: return a custom object so that names are immutable
