import json
import logging
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../")
import github
from irc import Colors


def Public(payload):

    colors = Colors()

    message = (
        "[{light_purple}{repo}{reset}] {dark_gray}{user}{reset} made the repository public\r\n"
    ).format(
        repo         = payload["repository"]["name"],
        user         = payload["sender"]["login"],
        dark_gray    = colors.dark_gray,
        light_purple = colors.light_purple,
        reset        = colors.reset
    )

    return {
        "statusCode": 200,
        "messages": [message]
    }
