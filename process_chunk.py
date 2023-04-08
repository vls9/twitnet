#!/usr/local/bin/python3
import os
from time import sleep, gmtime, strftime
import csv
import pandas as pd
from constants import (
    EDGELIST_FAILED_FNAME,
    EDGELIST_FNAME,
    EDGELIST_JOBS_FOLDER_NAME,
    NEXT_CHUNK_START_FNAME,
    NEXT_EDGELIST_JOB_FNAME,
    TWITTER_IDS_FNAME,
)
from utils.job_load import get_edgelist_job_dir_path
from utils.twitter_auth import get_twitter_api


def load_crontab_job_num():
    """
    Load the number of the current crontab job.
    """
    with open(
        f"{os.path.abspath(os.getcwd())}{EDGELIST_JOBS_FOLDER_NAME}{NEXT_EDGELIST_JOB_FNAME}",
        "r",
    ) as f:
        job_num = int(f.readline()) - 1
    print(f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tProcessing job {job_num}")
    return job_num


def load_chunk(job_dir, max_chunk_size=14):
    """
    Load chunk from the file. The start index of current chunk is specified in a separate file.
    """
    # Load start index of current chunk
    fname = f"{job_dir}{NEXT_CHUNK_START_FNAME}"
    if not os.path.exists(fname):
        with open(fname, "w") as f:
            start = 0
            f.write(str(start))
    else:
        with open(fname, "r") as f:
            start = int(f.readline())

    # Load chunk
    with open(f"{job_dir}{TWITTER_IDS_FNAME}", "r") as f:
        lines = list(f.readlines())
        id_list_len = len(lines)
        # Make sure start and end don't exceed length of ID list
        start = min(start, id_list_len)
        end = min(start + max_chunk_size, id_list_len)
        chunk = [line.strip() for line in lines[start:end]]
    print(
        f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tLoaded chunk from ID list, starting at line {start} of max size {max_chunk_size}"
    )
    return chunk


def process_chunk(api, chunk, job_dir, max_chunk_size=14, friends_limit=15000):
    """
    Process chunk of Twitter IDs.
    """
    failed = []
    # Initialize counters
    req_left = max_chunk_size  # min(max_chunk_size, len(chunk))
    max_requests_per_id = 3
    cur_cursor = -1
    explored = set()
    with open(f"{job_dir}{EDGELIST_FNAME}", "a") as f:
        writer = csv.writer(f)
        while len(chunk) > 0 and (req_left > 3 or (req_left < 4 and max_requests_per_id == 3)):
            # Pop ID from frontier
            id = chunk.pop(0)
            print("Selected ID:", id)
            res = []
            try:
                # Explore ID
                res = api.get_friend_ids(
                    user_id=id, stringify_ids=True, cursor=cur_cursor
                )
                print(
                    f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tExtracted {len(res[0])} friends of ID {id}"
                )
                sleep(2)
            except Exception as e:
                print("Exception:", repr(str(e)))
                print(
                    f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tFailed to load friends of ID {id}"
                )
                failed.append(
                    {"id_str": id, "error_message": str(e).split("\n")[0]})
            req_left -= 1

            # If next cursor isn't 0 (end of following list not reached)
            if res[1][1] != 0:
                if max_requests_per_id == 3:
                    # Get total number of accounts followed by user
                    user = api.get_user(user_id=id)._json
                    sleep(1)
                    print(f"User follows {user['friends_count']} accounts")
                    if user["friends_count"] > friends_limit:
                        failed.append(
                            {"id_str": id, "error_message": f"User follows over {friends_limit} accounts"}
                        )
                        print(
                            f"User {id} excluded because they follow over 15000 accounts")
                        # Reset counters
                        cur_cursor = -1
                        max_requests_per_id = 3
                    else:
                        cur_cursor = res[1][1]
                        chunk.insert(0, id)
                        max_requests_per_id -= 1
                        for friend_id in res[0]:
                            writer.writerow([id, friend_id])
                        explored.add(id)
                else:
                    cur_cursor = res[1][1]
                    chunk.insert(0, id)
                    max_requests_per_id -= 1
                    for friend_id in res[0]:
                        writer.writerow([id, friend_id])
                    explored.add(id)
            else:
                # Reset counters
                cur_cursor = -1
                max_requests_per_id = 3
                for friend_id in res[0]:
                    writer.writerow([id, friend_id])
                explored.add(id)

    # Save failed to file
    pd.DataFrame(failed).to_csv(
        f"{job_dir}{EDGELIST_FAILED_FNAME}", mode="a", header=False, index=False
    )
    print(
        f"Sent {max_chunk_size - req_left} requests to explore {len(explored)+len(failed)} users. {len(failed)} users were excluded")
    print(f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tChunk processed")
    return len(explored)


def move_next_chunk_start(job_dir, move_by):
    """
    Move the start index of next chunk.
    """
    fname = f"{job_dir}{NEXT_CHUNK_START_FNAME}"
    with open(fname, "r") as f:
        start = int(f.readline())
    print(f"New chunk size: {start} + {move_by} = {start+move_by}")
    with open(fname, "w") as f:
        f.write(str(start + move_by))
    return 0


api = get_twitter_api()
job_num = load_crontab_job_num()
job_dir = get_edgelist_job_dir_path(job_num)
chunk = load_chunk(job_dir, max_chunk_size=14)
move_by = process_chunk(api, chunk, job_dir, friends_limit=15000)
move_next_chunk_start(job_dir, move_by=move_by)
