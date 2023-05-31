# Twitnet: simple network analysis on Twitter

## Overview

This small Python app allows you to easily download follows (who-follows-whom) within a small Twitter network, plus perform a basic social network analysis (SNA) of the network, and visualize it.

## Prerequisites

You need a Twitter developer account. If you don't have one, [apply here](https://developer.twitter.com/en/portal/petition/essential/basic-info).

You also need the following Python libraries:

- `tweepy` (v4 and above),
- `networkx`,
- `pandas`.

You can run `pip3 install [library_name]` to install a missing library.

## Usage

Run scripts using `python3 [example.py]`. Below is a list of scripts.

Run this only once:

- `initialize.py` — create all necessary folders for the app, record your bearer token for the Twitter API.

At the beginning of your analysis, optionally run:

- `search.py` — find users from tweet search (optional).

Then, run these three steps until necessary (in this order):

- `load.py` — input or load user IDs,
- `process_chunk.py` — process chunk of user IDs (explore user IDs) (repeat until all user IDs are processed),
- `discover.py` — discover new user IDs to explore using community detection (optional).

Run this at the end:

- `analyze.py` — perform basic SNA and visualize the network (in development).

See the usage example below for more details!

## Usage example

### Step 1. `search.py`

Let's find some users who tweeted about Joe Biden in January 2017. The script prompts us for input:

```
Provide a Twitter search query:
joe biden
2023-04-08 10:27:18     Extracted 97 users from search query
Now run load.py, choose route 'c', depth '0', and insert this filename:

[working_directory]/files/joe_biden_201701010000_201703010000.csv
```

It found 97 users and recorded their IDs to a CSV file.

### Step 2. `load.py`

Let's load the recorded user IDs from the CSV file. The script asks us to provide the source:

```
Select source
        a : Twitter username(s)
        b : Twitter username list (CSV, TXT)
        c : Twitter ID list (CSV, TXT)
```

The source is an ID list in a CSV file, so let's choose option 'c' and provide the file name from the previous step. This will create a directory for the new job:

```
Provide local file path for Twitter ID list:
[working_directory]/files/joe_biden_201701010000_201703010000.csv
2023-04-08 10:33:15     Created new dir for edgelist job 6
2023-04-08 10:33:16     Loaded and recorded IDs from ID file
```

Skip the selection of "edgelist concatenation." Then, the script asks us to choose "depth":

```
Select ID set(s) to include (depth)
        0 : initial ID set only
        1 : all neighbors of initial ID set
Depth '1' is not recommended for sets of over 15 members
Enter '0' or '1'
0
```

Choosing depth '1' means adding all accounts followed by users in our ID list into the list. (This usually significantly increases the number of user IDs to process.) In this case, let's choose '0'.

Finally, the script provides some instructions on setting up a cron job on Linux-based operating systems. A cron job may be useful for large user ID lists.

### Step 3. `process_chunk.py`

Next, let's collect the follows between the users in our ID list. A list of follows is called the "edgelist."

The entire ID list may be too large to be processed at once, so the script will split it into chunks, such that it doesn't exceed Twitter API's rate limit (15 req./15 min, i.e. 1 req./1 min).

Note that due to another rate limit, users who follow over 15,000 accounts (need more than 3 requests per user ID) will be excluded and recorded in a separate file.

The output:

```
2023-04-08 10:46:03     Processing job 6
2023-04-08 10:46:03     Loaded chunk from ID list, starting at line 0 of max size 14
Selected ID: 184136149
2023-04-08 10:46:04     Extracted 5000 friends of ID 184136149
User follows 8528 accounts
Selected ID: 184136149
2023-04-08 10:46:07     Extracted 3528 friends of ID 184136149
Selected ID: 24920395
2023-04-08 10:46:10     Extracted 603 friends of ID 24920395
[...]
Sent 12 requests to explore 10 users. 0 users were excluded
2023-04-08 11:01:37     Chunk processed
```

The script explored 10 users (out of 97), sending 12 requests.

### Step 4. (optional) `discover.py`

At this point, we have all the follows between users in our ID list. Using this data, we can optionally analyze the community structure inside of this group of users. Community detection can help us find other users that are likely to be connected to the users from our ID list.

The script will use [the Girvan-Newman community detection algorithm](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.centrality.girvan_newman.html), and then select users who are followed by at least a fraction (e.g. 0.5, 0.8, 0.9) of the members of any community detected inside of our ID list. (Communities of less than 3 members are excluded.)

The script will ask us to choose this cutoff:

```
Specify cutoff percentile (e.g. 0.8, 0.66, 0.5): 0.8
```

For example, choosing 0.8 means that for a community of 6, a user is required to be followed by more than 4.8 of them (i.e. 5):

```
Community size: 6
In-degree cutoff: 4.8
```

Finally, the script gives us a summary of user discovery:

```
Added 37 users for exploration
Now run load.py, select option c (IDs from file) and paste this filename

[working_directory]/edgelist_jobs/6/discover_6_0_8.csv
```

The specified file includes the user IDs of "new users." We can use it to load the follows of these users, and then analyze the enlarged network.

### Step 5. (optional) Repeating exploration

To analyze the enlarged network, we need to collect the follows of "new users."

To do that, we can run `load.py` again, and load user IDs from the file provided in the previous step. This will create a new job.

To load the full enlarged network, with the follows of "old users," we have to load the follows of "old users" into our new job:

```
Concatenate edgelist from existing job? Specify job number or click Enter to skip:
6
```

Then, we can run `process_chunk.py` and `discover.py` again until we've fetched enough data for the analysis.

### Step 6. `analyze.py`

The script will prompt us to select groups of users (nodes in the network) to be filtered out:

```
Select group(s) of nodes to filter out
        a : outsiders
        b : original set
Type 'a' and/or 'b' or click Enter:
a
Number of unique sources: 26
Edgelist length before filtering: 114218
Edgelist length after filtering: 39
```

We should choose option 'a', filtering out outsiders, because we don't have the full data about them. (We have "insider → outsider" follows, but not "outsider → insider" follows.)

Then, the script will ask us whether to generate the "nodelist." The nodelist is data about Twitter users in the network, such their follower count or verified status.

Finally, the script outputs SNA results:

```
Number of unique sources: 96
Edgelist length before filtering: 170362
Edgelist length after filtering: 74
2023-04-08 13:04:50     Filtered out outsider nodes
2023-04-08 13:05:00     Extracted nodelist
2023-04-08 13:05:01     Saved nodelist to CSV
2023-04-08 13:05:01     Generated new nodelist for job 6
Nodes: 43
Edges: 74
2023-04-08 13:05:01     Set node attributes for graph for nodelist in job 6
Number of nodes: 43
Number of edges: 74
Maximum possible number of edges: 5402
Density: 0.04097452934662237
Transitivity: 0.22580645161290322
Strongly connected: False
Number of nodes outside the largest strongly connected component: 32
Diameter (of the largest strongly connected component): 3
2023-04-08 13:05:02     Graph visualized and file saved for job 6
```

We see that filtering out outsiders reduced the list of 170K follows to just 74. The number of users is reduced from 96 to 43, since many of the users don't follow and aren't followed by anyone within our ID list.

Then, the results of simple SNA are provided.

Finally, a simple network visualization will be saved in the `viz` folder inside the job directory.

## Important note

Please be careful not to infringe on Twitter user's privacy. The data accessed using this app is public but may still be sensitive.

## Contributions

All contributions are welcome.

(Section under construction.)
