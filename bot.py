
from apscheduler.schedulers.blocking import BlockingScheduler

from app.tasks import github_status, instagram, tiktok, twitter


sched = BlockingScheduler(timezone="Asia/Tokyo")


@sched.scheduled_job('interval', minutes=5)
def github_status_job():
    print('GitHubStatus: START!!')
    github_status.check()


@sched.scheduled_job('cron', hour='0-1,6-23', minute=30)
def tweet_job():
    print('START: Tweet')

    twitter.post_av_sommlier()
    twitter.post_av_actress()

    twitter.search_and_retweet('smash_bros')
    twitter.search_and_retweet('vtuber')
    twitter.search_and_retweet('splatoon')
    twitter.search_and_retweet('tiktok')


@sched.scheduled_job('cron', hour='*', minute=40)
def twitter_job():
    print('START: Twitter')

    account_list = [
        'av_sommlier',
        'av_actress',
        'smash_bros',
        'github',
        'vtuber',
        'splatoon',
        'tiktok',
    ]

    for account in account_list:

        try:
            twitter.remove_follow(account)
            twitter.follow_users_by_follower(account)
            twitter.follow_users_by_retweet(account)

        except Exception as e:
            pass

        print('FINISH: Twitter', account)


@sched.scheduled_job('cron', hour='8,20')
def instagram_job():
    print('Instagram START!!')
    instagram.get_location_japan()
    instagram.update_hashtag()
    instagram.add_hashtag_detail()
    print('Instagram FINISH!!')


@sched.scheduled_job('cron', hour='*')
def tiktok_job():
    print('TikTok START!!')
    tiktok.get_feed()
    tiktok.update_user_detail()


print("Scheduler START!!")
sched.start()
