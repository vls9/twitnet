import json
import os
from time import gmtime, strftime
from constants import CONFIG_FOLDER_NAME, EDGELIST_JOBS_FOLDER_NAME, FILES_FOLDER_NAME, NEXT_EDGELIST_JOB_FNAME, TWITTER_AUTH_FNAME
from utils.twitter_auth import get_twitter_api


def initialize_app(bearer_token=""):
    """
    Create all necessary folders.
    """
    # Create edgelist_jobs folder
    jobs_path = f"{os.path.abspath(os.getcwd())}{EDGELIST_JOBS_FOLDER_NAME}"
    os.mkdir(jobs_path)

    # Create next edgelist job file
    fname = f"{jobs_path}{NEXT_EDGELIST_JOB_FNAME}"
    with open(fname, "w") as f:
        num = 0
        f.write(str(num))

    # Create config
    config_path = f"{os.path.abspath(os.getcwd())}{CONFIG_FOLDER_NAME}"
    os.mkdir(config_path)

    # Save bearer token
    bearer_token_fname = f"{config_path}{TWITTER_AUTH_FNAME}"
    with open(bearer_token_fname, "w") as f:
        obj = {"bearer_token": bearer_token}
        json.dump(obj, f)

    # Create files dir
    os.mkdir(f"{os.path.abspath(os.getcwd())}{FILES_FOLDER_NAME}")
    print(
        f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tApp initialized"
    )
    return 0


bearer_token = input("Provide your Twitter bearer token token. Click Enter to skip\n")
if bearer_token:
    try:
        # Verify bearer token
        api = get_twitter_api(bearer_token=bearer_token)
        api.verify_credentials()
        initialize_app(bearer_token=bearer_token)
    except:
        initialize_app()
else:
    initialize_app()
