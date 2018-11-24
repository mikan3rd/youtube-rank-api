from app.tasks import tweet_crawl, twitter, twitter_tool


twitter.search_and_retweet('splatoon')

# exit()
# api = twitter.get_twitter_api('splatoon')

# twitter_tool.search_and_retweet(
#     username=api.username,
#     password=api.password,
#     status='人気ツイート',
#     query=api.query,
# )
