import os
from time import gmtime, strftime, strptime
import pandas as pd
from constants import FILES_FOLDER_NAME
from utils.twitter_auth import get_twitter_api


def get_users_from_query(api, query, result_type="mixed", max_results=100, min_follower_count=500):
    # Get tweets
    try:
        tweets = api.search_tweets(
            q=query, result_type=result_type, count=max_results)
        print(f"Number of tweets: {len(tweets)}")
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
        if (twt["user"]["followers_count"] >= min_follower_count):
            tweet_data.append(
                {
                    "id_str": twt["id_str"],
                    "user_id_str": twt["user"]["id_str"],
                    "user_screen_name": twt["user"]["screen_name"],
                    "user_followers_count": twt["user"]["followers_count"],
                    "user_frieds_count": twt["user"]["friends_count"],
                    "user_verified": twt["user"]["verified"],
                    "retweet_count": twt["retweet_count"],
                    "favorite_count": twt["favorite_count"],
                    "text_snippet": twt["text"],
                }
            )

    full_fname = f"{os.path.abspath(os.getcwd())}{FILES_FOLDER_NAME}full_tweet_data_{query.replace(' ', '_')}_{strftime('%Y_%m_%d__%H_%M_%S', gmtime())}.csv"
    pd.DataFrame(tweet_data).to_csv(full_fname, header=False, index=False)
    sorted_df = (
        pd.DataFrame(tweet_data)
        .sort_values(by="user_followers_count", ascending=False)
        .drop_duplicates(subset="user_screen_name")
    )
    # Save user IDs
    fname = f"{os.path.abspath(os.getcwd())}{FILES_FOLDER_NAME}{query.replace(' ', '_')}_{strftime('%Y_%m_%d__%H_%M_%S', gmtime())}.csv"
    sorted_df["user_id_str"].to_csv(fname, header=False, index=False)
    # Save tweet data
    td_fname = f"{os.path.abspath(os.getcwd())}{FILES_FOLDER_NAME}tweet_data_{query.replace(' ', '_')}_{strftime('%Y_%m_%d__%H_%M_%S', gmtime())}.csv"
    sorted_df.to_csv(td_fname, header=False, index=False)

    print(
        f"{strftime('%Y-%m-%d %H:%M:%S', gmtime())}\tExtracted {len(sorted_df)} users from search query"
    )
    print(
        f"Now run load.py, choose route 'c', depth '0', and insert this filename:\n\n{fname}\n")
    return sorted_df


api = get_twitter_api()
q = input("Provide a Twitter search query:\n")
get_users_from_query(api, query=q, result_type="mixed",
                     max_results=100)
