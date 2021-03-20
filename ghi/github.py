import json
import logging
import requests
from events.public import Public
from events.pull_request import PullRequest
from events.push import Push
from events.watch import Watch
from events.issues import Issues
from events.issue_comment import IssueComment


def getPool(payload, pools):

    try:
        payload = json.loads(payload)
    except json.JSONDecodeError as e:
        message = "There was a problem parsing payload: %s" % e
        logging.error(message)
        return {
            "statusCode": 400,
            "body": json.dumps({
                "success": False,
                "message": message
            })
        }
    ownerPool = None
    repo = payload["repository"]["full_name"]

    for pool in pools:
        if pool.containsRepo(repo):
            ownerPool = pool
            break

    if ownerPool is None:
        message = "Received repository '%s', but no pool is configured for it." % repo
        logging.info(message)
        return {
            "statusCode": 202,
            "body": json.dumps({
                "success": True,
                "message": message
            })
        }
    else:
        # get the secret for this repo
        for requestedRepo in ownerPool.repos:
            if repo == requestedRepo["name"]:
                repoName = requestedRepo["name"]
                repoSecret = requestedRepo["secret"]
                repoVerify = requestedRepo["verify"]
        logging.info("Matched repo '{}' to pool '{}'".format(repoName,ownerPool.name))
        return {
            "statusCode": 200,
            "pool": ownerPool,
            "name": repoName,
            "secret": repoSecret,
            "verify": repoVerify
        }


def shortenUrl(longUrl):
    gitIo = "https://git.io/create?url={}".format(longUrl)
    try:
        code = requests.post(gitIo)
        logging.debug(code.text)
        if code.status_code == 200:
            result = "https://git.io/{}".format(code.text)
        else:
            result = longUrl
    except Exception:
        result = longUrl
    return result


def parsePayload(event, payload, repos, shorten):

    # for every supported event: find the pool, parse the payload, and return IRC messages
    payload = json.loads(payload)
    logging.info("Received the '%s' event" % event)
    if event == "public":
        # Create messages based on the payload
        public = Public(payload, repos, shorten)
        if public["statusCode"] != 200:
            return public

        return {
            "statusCode": 200,
            "messages": public["messages"]
        }


    elif event == "push":
        # Create messages based on the payload
        push = Push(payload, repos, shorten)
        if push["statusCode"] != 200:
            return push

        return {
            "statusCode": 200,
            "messages": push["messages"]
        }


    elif event == "pull_request":
        # Create messages based on the payload
        pullRequest = PullRequest(payload, shorten)
        if pullRequest["statusCode"] != 200:
            return pullRequest

        return {
            "statusCode": 200,
            "messages": pullRequest["messages"]
        }


    elif event == "watch":
        # Create messages based on the payload
        watch = Watch(payload, shorten)
        if watch["statusCode"] != 200:
            return watch

        return {
            "statusCode": 200,
            "messages": watch["messages"]
        }


    elif event == "issues":
        # Create messages based on the payload
        issues = Issues(payload, shorten)
        if issues["statusCode"] != 200:
            return issues

        return {
            "statusCode": 200,
            "messages": issues["messages"]
        }


    elif event == "issue_comment":
        # Create messages based on the payload
        issue_comment = IssueComment(payload, shorten)
        if issue_comment["statusCode"] != 200:
            return issue_comment

        return {
            "statusCode": 200,
            "messages": issue_comment["messages"]
        }


    elif event == "ping":
        logging.info("Sent 'pong'")
        return {
            "statusCode": 202,
            "messages": "pong"
        }


    else:
        message = "Received event '%s'. Doing nothing." % event
        logging.info(message)
        return {
            "statusCode": 202,
            "body": json.dumps({
                "success": True,
                "message": message
            })
        }
