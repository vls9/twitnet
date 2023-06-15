import os
from time import gmtime, strftime
from constants import EDGELIST_FAILED_FNAME, FILES_FOLDER_NAME, TWITTER_IDS_FAILED_FNAME
from utils.job_load import get_edgelist_job_dir_path, get_job_num

job_num = get_job_num()
job_dir = get_edgelist_job_dir_path(job_num)
failed_path = f"{job_dir}{EDGELIST_FAILED_FNAME}"
to_retry = set()
with open(failed_path, "r") as f:
    for line in f.readlines():
        if "Unauthorized" not in line and "User follows over" not in line:
            to_retry.add(f"{line.split(',')[0]}\n")
file_path = f"{os.path.abspath(os.getcwd())}{FILES_FOLDER_NAME}to_retry_{job_num}_{strftime('%Y_%m_%d__%H_%M_%S', gmtime())}.csv"
with open(file_path, "w") as f:
    f.writelines(to_retry)
print(f"Recorded {len(to_retry)} IDs to retry")
print(
    f"Now run load.py, select route c and paste this filename:\n\n{file_path}\n")
