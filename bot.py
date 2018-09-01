from apscheduler.schedulers.blocking import BlockingScheduler

from app.tasks import test


sched = BlockingScheduler()


@sched.scheduled_job('interval', minutes=3)
def timed_job():
    print('This job runs every three minutes.')


@sched.scheduled_job('cron', hour=0)
def job_3min():
    print('Instagram Update!!')
    test.uptdate_hashtag()


sched.start()
