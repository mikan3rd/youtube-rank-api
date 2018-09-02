from apscheduler.schedulers.blocking import BlockingScheduler

from app.tasks import instagram


sched = BlockingScheduler(timezone="Asia/Tokyo")


@sched.scheduled_job('cron', hour='8,20')
def instagram_job():
    print('Instagram START!!')
    instagram.update_hashtag()
    instagram.add_hashtag_detail()
    print('Instagram FINISH!!')


sched.start()
print("Scheduler START!!")
