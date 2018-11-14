
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

    smash_bros_query = '(スマブラSP) (filter:images OR filter:videos) min_retweets:10'
    twitter.search_and_retweet('smash_bros', smash_bros_query)

    words = [
        "vtuber"
        "バーチャルYouTuber",
        "KizunaAI",
        "キズナアイ",
        "輝夜月",
        "電脳少女シロ",
        "SiroArt",
        "ミライアカリ",
        "バーチャルのじゃロリ狐娘youtuberおじさん",
        "Nora_Cat",
        "のらきゃっと",
        "みとあーと",
        "猫宮ひなた",
        "HinataCat",
        "soraArt",
        "ばあちゃる",
        "鳩羽つぐ",
    ]
    vtuber_query = '(%s) (filter:images OR filter:videos) min_retweets:50' \
        % (' OR '.join(words))
    twitter.search_and_retweet('vtuber', vtuber_query)

    splatoon_query = '#Splatoon2 filter:videos min_retweets:10'
    twitter.search_and_retweet('splatoon', splatoon_query)


@sched.scheduled_job('cron', hour='*', minute=30)
def twitter_job():
    print('START: Twitter')

    account_list = [
        'av_sommlier',
        'av_actress',
        'smash_bros',
        'github',
        'vtuber',
        'splatoon',
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
