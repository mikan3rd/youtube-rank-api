
from apscheduler.schedulers.blocking import BlockingScheduler

from app.tasks import github_status, instagram, tiktok, twitter


sched = BlockingScheduler(timezone="Asia/Tokyo")


@sched.scheduled_job('interval', minutes=5)
def github_status_job():
    print('GitHubStatus: START!!')
    github_status.check()


@sched.scheduled_job('cron', hour='*', minute=30)
def twitter_job():
    print('START: Twitter')

    twitter.post_av_sommlier()
    twitter.post_av_actress()

    account_list = [
        'av_sommlier',
        'av_actress',
    ]

    for account in account_list:
        twitter.remove_follow(account)
        twitter.follow_users_by_follower(account)
        twitter.follow_users_by_retweet(account)
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
