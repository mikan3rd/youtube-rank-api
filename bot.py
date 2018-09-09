from datetime import datetime
from time import sleep

from apscheduler.schedulers.blocking import BlockingScheduler

from app.tasks import instagram, qiita, tiktok


sched = BlockingScheduler(timezone="Asia/Tokyo")


@sched.scheduled_job('cron', hour='8,20')
def instagram_job():
    print('Instagram START!!')
    instagram.get_location_japan()
    instagram.update_hashtag()
    instagram.add_hashtag_detail()
    print('Instagram FINISH!!')


@sched.scheduled_job('interval', minutes=10)
def tiktok_job():
    print('TikTok START!!')
    tiktok.update_user_detail()
    tiktok.get_feed()


print("Scheduler START!!")
sched.start()
