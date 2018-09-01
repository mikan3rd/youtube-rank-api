from apscheduler.schedulers.blocking import BlockingScheduler

from app.tasks import instagram


sched = BlockingScheduler(timezone="Asia/Tokyo")


# @sched.scheduled_job('interval', minutes=3)
# def timed_job():
#     print('This job runs every three minutes.')


@sched.scheduled_job('cron', hour=6)
def instagram_job():
    print('Instagram START!!')
    instagram.update_hashtag()
    instagram.add_hashtag_detail()
    print('Instagram FINISH!!')


sched.start()
