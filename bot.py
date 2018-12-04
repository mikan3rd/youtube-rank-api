
from apscheduler.schedulers.blocking import BlockingScheduler

from app.tasks import instagram, tiktok, tweet_crawl, twitter


sched = BlockingScheduler(timezone="Asia/Tokyo")


@sched.scheduled_job('interval', minutes=5)
def github_status_job():
    print('GitHubStatus: START!!')
    tweet_crawl.github_status()


@sched.scheduled_job('cron', hour='0-1,6-23', minute=1)
def tweet_job():
    print('START: Tweet')

    twitter.post_av_sommlier()
    twitter.post_av_actress()

    twitter.search_and_retweet('vtuber')
    twitter.search_and_retweet('splatoon')
    twitter.search_and_retweet('smash_bros')
    twitter.search_and_retweet('hypnosismic')

    twitter.tweet_affiliate('rakuten_rank')

    twitter.tweet_tiktok()


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


@sched.scheduled_job('cron', hour='7,12,17,20,23', minute=30)
def twitter_job():
    print('START: Follow')

    account_list = [
        'av_sommlier',
        'av_actress',
        'smash_bros',
        'github',
        'vtuber',
        'splatoon',
        'tiktok',
        'hypnosismic',
        'rakuten_rank',
    ]

    for account in account_list:

        try:
            twitter.remove_follow(account)
            twitter.follow_users_by_follower(account)
            # twitter.follow_users_by_retweet(account)
            twitter.follow_target_user(account)

        except Exception as e:
            pass

        print('FINISH: Twitter', account)

    tweet_crawl.hypnosismic()


# @sched.scheduled_job('cron', hour='8,20')
# def instagram_job():
#     print('Instagram START!!')
#     instagram.get_location_japan()
#     instagram.update_hashtag()
#     instagram.add_hashtag_detail()
#     print('Instagram FINISH!!')


@sched.scheduled_job('cron', hour='*', minute=15)
def tiktok_job():
    print('TikTok START!!')
    tiktok.add_user()
    tiktok.update_users()
    tiktok.add_hashtag()


print("Scheduler START!!")
sched.start()
