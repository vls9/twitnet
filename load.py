import os
from time import sleep, gmtime, strftime
import csv
from constants import (
    CONCAT_FNAME,
    EDGELIST_FNAME,
    EDGELIST_JOBS_FOLDER_NAME,
    NEXT_EDGELIST_JOB_FNAME,
    TWITTER_IDS_FAILED_FNAME,
    TWITTER_IDS_FNAME,
    TWITTER_IDS_ORIGINAL_FNAME,
)
from utils.job_load import get_edgelist_job_dir_path
from utils.twitter_auth import get_twitter_api


def pick_route():
    """
    Pick application route.
    """
    entered = input(
        "Select source\n\ta : Twitter username(s)\n\tb : Twitter username list (CSV, TXT)\n\tc : Twitter ID list (CSV, TXT)\nType 'a', 'b' or 'c': "
    )
    if entered not in ["a", "b", "c"]:
        pick_route()
    else:
        print(
            f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tSelected app route {entered}"
        )
        return entered


def get_usernames_from_input():
    """
    Input Twitter username(s).
    """
    usernames = (
        input("Provide Twitter username(s) separated by whitespace:\n")
        .replace("@", "")
        .split()
    )
    if not usernames:
        get_usernames_from_input()
    else:
        return usernames


def get_usernames_from_file():
    """
    Load list of Twitter usernames from file. Note: CSV or TXT file must not have a header row.
    """
    path = input("Provide file path for Twitter username list:\n")
    if not path or not os.path.exists(path):
        get_usernames_from_file()
    else:
        with open(path, "r") as f:
            usernames = [line.replace("@", "").strip()
                         for line in list(f.readlines())]
        return usernames


def get_ids_from_usernames(api, usernames):
    """
    Find the user's Twitter ID by username.
    """
    failed = set()
    # Make directory for new edgelist job and load its path
    job_num = make_edgelist_job_dir()
    job_dir = get_edgelist_job_dir_path(job_num)
    loaded_path = f"{job_dir}{TWITTER_IDS_FNAME}"
    failed_path = f"{job_dir}{TWITTER_IDS_FAILED_FNAME}"
    with open(loaded_path, "a") as f:
        writer = csv.writer(f)
        for username in usernames:
            # Attempt to load user object and get ID
            try:
                user = api.get_user(screen_name=username)
                # Write it to CSV
                writer.writerow([user.id])
            except:
                failed.add(username)
            sleep(0.2)
    if failed:
        handle_failed(failed, failed_path)
    print(
        f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tLoaded and recorded IDs for {len(usernames)} usernames"
    )
    return job_num


def handle_failed(failed, failed_path):
    """
    Record usernames of users not found.
    """
    with open(failed_path, "a") as f:
        writer = csv.writer(f)
        for username in failed:
            writer.writerow([username])
    print(
        f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tFailed to load IDs for {len(failed)} usernames"
    )
    return 0


def get_ids_from_file():
    """
    Load list of Twitter IDs from file. Note: CSV or TXT file must not have a header row.
    """
    path = input("Provide local file path for Twitter ID list:\n")
    if not path or not os.path.exists(path):
        print("File not found")
        get_ids_from_file()
    else:
        # Check the number of columns in the first line
        with open(path, "r") as f:
            n_cols = len(f.readline().split(","))
        if n_cols != 1:
            print("File has more than one column (commas found)")
            get_ids_from_file()
        else:
            job_num = make_edgelist_job_dir()
            job_dir = get_edgelist_job_dir_path(job_num)
            # Copy file, wait for copying to execute
            os.popen(f"cp {path} {job_dir}{TWITTER_IDS_FNAME}")
            sleep(1)
            print(
                f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tLoaded and recorded IDs from ID file"
            )
            return job_num


def make_edgelist_job_dir():
    """
    Load and update the next edgelist job number.
    """
    # Get current egdelist job number
    jobs_path = f"{os.path.abspath(os.getcwd())}{EDGELIST_JOBS_FOLDER_NAME}"
    fname = f"{jobs_path}{NEXT_EDGELIST_JOB_FNAME}"
    with open(fname, "r") as f:
        num = int(f.readline())
    with open(fname, "w") as f:
        f.write(str(num + 1))

    # Make dir for new edgelist job
    path = f"{jobs_path}{num}/"
    os.mkdir(path)
    print(
        f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tCreated new dir for edgelist job {num}"
    )
    return num


def expand_network(api, job_dir):
    """
    Optionally expand the network, adding users followed by users from the original set.
    """
    depth = input(
        "Select ID set(s) to include (depth)\n\t0 : initial ID set only\n\t1 : all neighbors of initial ID set\nDepth '1' is not recommended for sets of over 15 members\nEnter '0' or '1'\n"
    )
    if not depth:
        depth = "0"
    if depth in ["0", "1"]:
        if depth == "1":
            # Copy IDs file of the original set
            os.popen(
                f"cp {job_dir}{TWITTER_IDS_FNAME} {job_dir}{TWITTER_IDS_ORIGINAL_FNAME}"
            )
            sleep(1)
            print(
                f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tCopied {TWITTER_IDS_FNAME}"
            )
            with open(f"{job_dir}{TWITTER_IDS_FNAME}", "r") as f:
                chunk = [line.strip() for line in list(f.readlines())]
            with open(f"{job_dir}{TWITTER_IDS_FNAME}", "a") as f:
                for id in chunk:
                    try:
                        friend_ids = api.get_friend_ids(
                            user_id=id, stringify_ids=True)
                        for friend_id in friend_ids:
                            f.write(f"{friend_id}\n")
                        print(
                            f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tExtracted {len(friend_ids)} accounts followed by user {id}, appended them to twitter_ids.csv"
                        )
                        # Ensure rate limit is not exceeded
                        sleep(2)
                    except:
                        print(f"Failed to load friends of user {id}")
            return 0
        return 0
    else:
        expand_network()


def calculate_maximum_completion_time(job_dir, chunk_size=14):
    """
    Estimate maximum time to complete data collection.
    """
    # Compute size of entire network
    with open(f"{job_dir}{TWITTER_IDS_FNAME}", "r") as f:
        size = len(f.readlines())
    # Compute estimated time to complete (in hours)
    interval = chunk_size + 1
    if size < interval:
        est_time = 0.00
    else:
        est_time = round(size / (interval * 4), 2) * 3
    print(f"Maximum completion time: {est_time}")
    return est_time


def help_setup_crontab(job_dir):
    """
    Print out a crontab setup guide.
    """
    minute = int(strftime("%M", gmtime()))
    minutes = sorted([(minute + 3 + (15 * i)) % 60 for i in range(4)])
    print("To install a crontab, run `crontab -e`, click `i` to edit, and add:\n")
    print(
        f"{','.join(str(i) for i in minutes)} * * * * cd {'/'.join(job_dir.split('/')[:-3])} && ./cron_chunk.sh >> {job_dir}cron_out.txt 2>&1"
    )
    print("\nTo uninstall the crontab, comment out (`#`) or remove the line")
    print(
        "To exit crontab, hit `esc` and type `:wq`\nTo view active crontabs, run `crontab -l`"
    )
    print("Make sure that machine stays connected to the Internet")
    return 0


def concat_edgelists(job_dir_a, job_dir_b):
    """
    Concatenate two edgelists from different jobs.
    """
    # Verify that job_num_b exists
    if not os.path.exists(job_dir_b):
        print("Job dir B doesn't exist")
        return 1

    # Get all edgelists concatted with job B, if it has any
    concat_b_fname = f"{job_dir_b}{CONCAT_FNAME}"
    concat_b = []
    if os.path.exists(concat_b_fname):
        with open(concat_b_fname, "r") as f:
            concat_b.extend(f.readlines())

    # Verify that filenames in concat_b are correct
    for i in concat_b:
        try:
            if not os.path.exists(i.strip()):
                raise Exception("Incorrect filename")
        except Exception as e:
            print("Exception:", e)
            print("Failed to verify filenames")
            return 1

    # Write job_dir_b to file
    concat_a_fname = f"{job_dir_a}{CONCAT_FNAME}"
    with open(concat_a_fname, "a") as f:
        concat_b.append(f"{job_dir_b}{EDGELIST_FNAME}\n")
        f.writelines(concat_b)

    print(
        f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tSuccessfully concatenated edgelists for two job dirs"
    )

    return 0


route = pick_route()
api = get_twitter_api()
if route == "a":
    usernames = get_usernames_from_input()
    job_num = get_ids_from_usernames(api, usernames)
    job_dir = get_edgelist_job_dir_path(job_num)
elif route == "b":
    usernames = get_usernames_from_file()
    job_num = get_ids_from_usernames(api, usernames)
    job_dir = get_edgelist_job_dir_path(job_num)
else:
    job_num = get_ids_from_file()
    job_dir = get_edgelist_job_dir_path(job_num)
    job_num_b_input = input(
        "Concatenate edgelist from existing job? Specify job number or click Enter to skip:\n")
    if job_num_b_input:
        job_dir_b = get_edgelist_job_dir_path(int(job_num_b_input))
        concat_edgelists(job_dir, job_dir_b)
expand_network(api, job_dir)
calculate_maximum_completion_time(job_dir, chunk_size=14)
help_setup_crontab(job_dir)
