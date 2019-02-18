
from apscheduler.schedulers.blocking import BlockingScheduler

from app.tasks import instagram, tiktok, tweet_crawl, twitter


sched = BlockingScheduler(timezone="Asia/Tokyo")


# @sched.scheduled_job('interval', minutes=5)
# def github_status_job():
#     print('GitHubStatus: START!!')
#     tweet_crawl.github_status()


@sched.scheduled_job('cron', hour='*', minute=1)
def tweet_job():
    print('START: Tweet')

    twitter.tweet_affiliate('rakuten_rank')

    twitter.search_and_retweet('vtuber')
    twitter.search_and_retweet('splatoon')
    twitter.search_and_retweet('smash_bros')
    twitter.search_and_retweet('hypnosismic')
    twitter.search_and_retweet('tiktok')
    twitter.search_and_retweet('trend_video')

    twitter.post_av_actress()

    twitter.retweet_user('av_sommlier')

    tweet_crawl.hypnosismic()
    tweet_crawl.smash_bros()

    twitter.tweet_rakuten_travel()


@sched.scheduled_job('cron', hour='7,12,17,20,23', minute=5)
def tweet_affiliate():
    print('START: tweet_affiliate')

    account_list = [
        'vtuber',
        'splatoon',
        'smash_bros',
        'hypnosismic',
        'tiktok',
        'av_actress',
    ]

    for account in account_list:
        twitter.tweet_affiliate(account)

    twitter.retweet_user('rakuten_rank', '_rakuten_travel')
    twitter.retweet_user('av_sommlier', '_rakuten_rank')
    twitter.retweet_user('rakuten_travel', '_rakuten_rank')
    twitter.retweet_user('trend_video', '_rakuten_rank')


@sched.scheduled_job('cron', hour='*/6', minute=30)
def twitter_job():
    print('START: Follow')

    account_list = [
        'vtuber',
        'splatoon',
        # 'tiktok',
        # 'hypnosismic',
        # 'smash_bros',
        # 'rakuten_rank',
        # 'av_actress',
        # 'av_sommlier',
        # 'trend_video',
        'github',
    ]

    for account in account_list:

        twitter.remove_follow(account)
        # twitter.follow_users_by_follower(account)
        # twitter.follow_target_user(account)
        # twitter.follow_users_by_retweet(account)

        print('FINISH: Twitter', account)


@sched.scheduled_job('cron', hour='*/6', minute=10)
def twitter_favorite_job():
    print('START: Twitter Favorite')

    account_list = [
        'vtuber',
        'splatoon',
        'smash_bros',
        'tiktok',
        'hypnosismic',
        'rakuten_rank',
        'rakuten_travel',
        'av_actress',
        'av_sommlier',
        'trend_video',
        'github',
    ]

    for account in account_list:
        twitter.favorite_tweet(account)


@sched.scheduled_job('cron', hour='*/3', minute=5)
def twitter_video_job():
    print('START: Twitter VIDEO')

    twitter.post_av_sommlier()
    twitter.tweet_tiktok_video()
    twitter.retweet_user('av_actress')


@sched.scheduled_job('cron', hour='8,20')
def twitter_health_check():
    print('START: Twitter Health Check')
    twitter.health_check()


# @sched.scheduled_job('cron', hour='8,20')
# def instagram_job():
#     print('Instagram START!!')
#     instagram.get_location_japan()
#     instagram.update_hashtag()
#     instagram.add_hashtag_detail()
#     print('Instagram FINISH!!')


@sched.scheduled_job('cron', hour='*', minute='15,45')
def tiktok_job():
    print('TikTok START!!')
    tiktok.add_user()
    tiktok.update_users()
    # tiktok.trace_hashtag()


@sched.scheduled_job('cron', hour='3')
def oneday_job():
    print('START: oneday_job')
    account_list = [
        'vtuber',
        'splatoon',
        'smash_bros',
        'tiktok',
        'hypnosismic',
        # 'rakuten_rank',
        'rakuten_travel',
        # 'av_actress',
        # 'av_sommlier',
        'trend_video',
        'github',
    ]

    for account in account_list:
        twitter.add_list()

#     tiktok.add_hashtag()
#     tiktok.update_spread_sheet()


print("Scheduler START!!")
sched.start()
