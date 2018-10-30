
from apscheduler.schedulers.blocking import BlockingScheduler

from app.tasks import github_status, instagram, tiktok


sched = BlockingScheduler(timezone="Asia/Tokyo")


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


@sched.scheduled_job('interval', minutes=5)
def github_status_job():
    print('GitHubStatus: START!!')
    github_status.check()


print("Scheduler START!!")
sched.start()
