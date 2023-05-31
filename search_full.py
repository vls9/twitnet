import os
from time import gmtime, strftime, strptime
import pandas as pd
from constants import FILES_FOLDER_NAME
from utils.twitter_auth import get_twitter_api


def get_users_from_query(api, query, label="dev", max_results=100, from_date=None, to_date=None):
    # Get tweets
    try:
        if from_date and to_date:
            tweets = api.search_full_archive(
                query=query, label=label, maxResults=max_results, fromDate=from_date, toDate=to_date
            )
        else:
            tweets = api.search_full_archive(
                query=query, label=label, maxResults=max_results
            )
        if not tweets:
            print("No tweets found")
            return 1
    except Exception as e:
        print("Exception:", e)
        print("Couldn't load tweets from the API")
        return 1

    tweet_data = []
    for tweet in tweets:
        twt = tweet._json
        tweet_data.append(
            {
                "id_str": twt["id_str"],
                "user_id_str": twt["user"]["id_str"],
                "user_screen_name": twt["user"]["screen_name"],
                "user_followers_count": twt["user"]["followers_count"],
                "user_frieds_count": twt["user"]["friends_count"],
                "user_verified": twt["user"]["verified"],
                "quote_count": twt["quote_count"],
                "reply_count": twt["reply_count"],
                "retweet_count": twt["retweet_count"],
                "favorite_count": twt["favorite_count"],
                "text_snippet": twt["text"],
            }
        )

    sorted_df = (
        pd.DataFrame(tweet_data)
        .sort_values(by="user_followers_count", ascending=False)
        .drop_duplicates(subset="user_screen_name")
    )
    # Save user IDs
    fname = f"{os.path.abspath(os.getcwd())}{FILES_FOLDER_NAME}{query.replace(' ', '_')}_{from_date}_{to_date}.csv"
    sorted_df["user_id_str"].to_csv(fname, header=False, index=False)
    # Save tweet data
    td_fname = f"{os.path.abspath(os.getcwd())}{FILES_FOLDER_NAME}tweet_data_{query.replace(' ', '_')}_{from_date}_{to_date}.csv" 
    sorted_df.to_csv(td_fname, header=False, index=False)

    print(
        f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tExtracted {len(sorted_df)} users from search query"
    )
    print(f"Now run load.py, choose route 'c', depth '0', and insert this filename:\n\n{fname}\n")
    return sorted_df


api = get_twitter_api()
q = input("Provide a Twitter search query:\n")
from_date = strftime("%Y%m%d%H%M", strptime(
    input("Provide a start date (format: YYYY-MM-DD) or click Enter to skip:\n"), "%Y-%m-%d"))
to_date = strftime("%Y%m%d%H%M", strptime(
    input("Provide an end date (not included) (format: YYYY-MM-DD) or click Enter to skip:\n"), "%Y-%m-%d"))
get_users_from_query(api, query=q, label="dev",
                     max_results=100, from_date=from_date, to_date=to_date)
