import json
import os
import tweepy

from constants import CONFIG_FOLDER_NAME, TWITTER_AUTH_FNAME


def get_twitter_api(bearer_token=""):
    """
    Get the tweepy API object using the bearer token from a Twitter developer account.
    """
    if int(tweepy.__version__.split(".")[0]) < 4:
        print(f"Please update tweepy to v4. Your current version is: {tweepy.__version__}")
    if not bearer_token:
        # Load bearer token from config file
        with open(f"{os.path.abspath(os.getcwd())}{CONFIG_FOLDER_NAME}{TWITTER_AUTH_FNAME}", "r") as f:
            bearer_token = json.load(f)["bearer_token"]
    # Authenticate to Twitter API v1.1
    auth = tweepy.OAuth2BearerHandler(bearer_token)
    api = tweepy.API(auth)
    return api