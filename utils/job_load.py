import os
from time import gmtime, strftime
import pandas as pd
from constants import CONCAT_FNAME, EDGELIST_FAILED_FNAME, EDGELIST_FNAME, EDGELIST_JOBS_FOLDER_NAME, NEXT_EDGELIST_JOB_FNAME


def get_job_num():
    """
    Input a job number or find the most recent one.
    """
    job_num = input(
        "Specify job number. For the most recent crontab job, click Enter\nEnter job number or click Enter: "
    )
    if not job_num:
        with open(f"{os.path.abspath(os.getcwd())}{EDGELIST_JOBS_FOLDER_NAME}{NEXT_EDGELIST_JOB_FNAME}", "r") as f:
            job_num = int(f.readline()) - 1
    else:
        try:
            job_num = int(job_num)
        except:
            get_job_num()
    print(f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tSelected job {job_num}")
    return job_num


def get_edgelist_job_dir_path(job_num):
    """
    Get the full path of a job dir based on its number.
    """
    return f"{os.path.abspath(os.getcwd())}{EDGELIST_JOBS_FOLDER_NAME}{job_num}/"


def load_edgelist(job_dir):
    """
    Load edgelist from specified job dir.
    """

    # Load edgelists from other jobs based on concat file
    concat_fname = f"{job_dir}{CONCAT_FNAME}"
    dfs = []
    if os.path.exists(concat_fname):
        with open(concat_fname, "r") as f:
            dfs = [pd.read_csv(i.strip(), names=["source", "target"], dtype={
                            "source": str, "target": str}) for i in f.readlines()]
    try:
        # Load edgelist from current job
        df_og = pd.read_csv(
            f"{job_dir}{EDGELIST_FNAME}",
            names=["source", "target"],
            dtype={"source": str, "target": str},
        )
        dfs.append(df_og)
    except FileNotFoundError:
        pass
    df = pd.concat(dfs)

    # df = pd.read_csv(
    #     f"{job_dir}{EDGELIST_FNAME}",
    #     names=["source", "target"],
    #     dtype={"source": str, "target": str},
    # )
    return df


def load_failed(job_dir):
    """
    Load user IDs that failed to fetch from specified job dir.
    """
    fname = f"{job_dir}{EDGELIST_FAILED_FNAME}"
    with open(fname, "r") as f:
        failed = [line.strip() for line in f.readlines()]
    return failed
