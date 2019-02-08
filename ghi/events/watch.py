import json
import logging
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../")
import github
from irc import Colors


def Watch(payload, shorten):

    action = payload["action"]
    logging.info("Received action '%s'" % action)
    colors = Colors()

    if action == "started":
        message = (
            "[{light_purple}{repo}{reset}] {dark_gray}{user}{reset} started starring. New stargazers count: {stargazers}\r\n"
        ).format(
            repo         = payload["repository"]["name"],
            user         = payload["sender"]["login"],
            stargazers   = payload["repository"]["stargazers_count"],
            light_gray   = colors.light_gray,
            dark_gray    = colors.dark_gray,
            light_purple = colors.light_purple,
            dark_purple  = colors.dark_purple,
            underline    = colors.underline,
            bold         = colors.bold,
            reset        = colors.reset
        )

        return {
            "statusCode": 200,
            "messages": [message]
        }

    else:
        message = "Watch Action was %s. Doing nothing." % action
        logging.info(message)
        return {
            "statusCode": 202,
            "body": json.dumps({
                "success": True,
                "message": message
            })
        }
