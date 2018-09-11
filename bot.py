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
    tiktok.get_feed()
    tiktok.update_user_detail()


@sched.scheduled_job('cron', hour=9)
def qiita_job():
    print('Qiita START!!')
    body = tiktok.create_markdown()
    now = datetime.now().strftime("%Y/%m/%d")
    title = '【自動更新】TikTok人気ユーザーランキング【%s】' % (now)
    tags = [{'name': 'Python'}, {'name': 'ランキング'}, {'name': '自動生成'}, {'name': 'tiktok'}]

    qiita.patch_item(
        item_id="b34002f5a9ecaaaacf09",
        title=title,
        body=body,
        tags=tags,
    )


print("Scheduler START!!")
sched.start()
