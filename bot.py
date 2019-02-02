
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

    twitter.post_av_actress()

    twitter.retweet_user('av_sommlier')


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

        try:
            twitter.tweet_affiliate(account)

        except Exception as e:
            pass

        print('FINISH: tweet_affiliate', account)

    twitter.post_av_sommlier()
    twitter.tweet_tiktok_video()

    twitter.retweet_user('av_actress')
    twitter.retweet_user('av_sommlier', '_rakuten_rank')


@sched.scheduled_job('cron', hour='0,12,15,18,21', minute=30)
def twitter_job():
    print('START: Follow')

    account_list = [
        'vtuber',
        'splatoon',
        'tiktok',
        'hypnosismic',
        'rakuten_rank',
        'av_actress',
        'av_sommlier',
        'smash_bros',
        'github',
    ]

    for account in account_list:

        try:
            twitter.remove_follow(account)
            # twitter.follow_users_by_follower(account)
            # twitter.follow_target_user(account)
            # twitter.follow_users_by_retweet(account)

        except Exception as e:
            pass

        print('FINISH: Twitter', account)

    tweet_crawl.hypnosismic()


@sched.scheduled_job('cron', hour='*/2', minute=10)
def twitter_favorite_job():
    print('START: Twitter Favorite')

    account_list = [
        'vtuber',
        'splatoon',
        'tiktok',
        'hypnosismic',
        'rakuten_rank',
        'av_actress',
        'av_sommlier',
        'smash_bros',
        'github',
    ]

    for account in account_list:

        try:
            twitter.favorite_tweet(account)

        except Exception as e:
            pass


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
    # tiktok.update_users()
    # tiktok.trace_hashtag()


@sched.scheduled_job('cron', hour='3')
def oneday_job():
    pass
    # tiktok.add_hashtag()
    # tiktok.update_spread_sheet()


print("Scheduler START!!")
sched.start()
