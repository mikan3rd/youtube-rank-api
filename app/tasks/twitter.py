import json
import re
import urllib.request
from datetime import datetime
from pprint import pprint
from random import choice, randint, shuffle
from time import sleep, time

import cv2
import redis
import requests
from bs4 import BeautifulSoup
from firebase_admin import firestore
from selenium.webdriver import Chrome, ChromeOptions
from settings import (
    DRIVER_PATH,
    GOOGLE_CHROME_PATH,
    REDIS_URL,
    TWITTER_AV_ACTRESS_ACCESS_TOKEN,
    TWITTER_AV_ACTRESS_SECRET,
    TWITTER_AV_SOMMLIER_ACCESS_TOKEN,
    TWITTER_AV_SOMMLIER_SECRET,
    TWITTER_GITHUB_ACCESS_TOKEN,
    TWITTER_GITHUB_SECRET,
    TWITTER_HYPNOSISMIC_ACCESS_TOKEN,
    TWITTER_HYPNOSISMIC_SECRET,
    TWITTER_PASSWORD_A,
    TWITTER_PASSWORD_B,
    TWITTER_RAKUTEN_RANK_ACCESS_TOKEN,
    TWITTER_RAKUTEN_RANK_SECRET,
    TWITTER_SMASH_BROS_ACCESS_TOKEN,
    TWITTER_SMASH_BROS_SECRET,
    TWITTER_SPLATOON_SECRET,
    TWITTER_SPLATTON_ACCESS_TOKEN,
    TWITTER_TIKTOK_ACCESS_TOKEN,
    TWITTER_TIKTOK_SECRET,
    TWITTER_VTUBER_ACCESS_TOKEN,
    TWITTER_VTUBER_SECRET
)

from app.server.helpers import firestore as helper_firestore
from app.server.helpers import dmm, rakuten
from app.server.helpers.twitter import TwitterApi


def post_av_sommlier():
    api = get_twitter_api('av_sommlier')

    redis_key = 'twitter:av_movie'
    r = redis.from_url(REDIS_URL)
    rcache = r.get(redis_key)

    id_list = []
    if rcache:
        print("cache HIT!! %s" % (redis_key))
        id_list = json.loads(rcache.decode())

    target = None
    filename = 'trial_video.mp4'

    hits = 100
    for i in range(10):
        response = dmm.search_items(offset=i * hits + 1)

        for item in response['result']['items']:
            if item['product_id'] not in id_list and item.get('sampleMovieURL'):
                movie_url = item['sampleMovieURL'].get('size_720_480')
                print(movie_url)

                try:
                    response = requests.get(movie_url)
                    soup = BeautifulSoup(response.content, "lxml")
                    iframe_tag = soup.find('iframe')
                    iframe_url = 'https:' + iframe_tag.get('src')

                    driver = get_driver()
                    driver.get(iframe_url)
                    html_source = driver.page_source
                    soup = BeautifulSoup(html_source, "lxml")
                    video_tag = soup.find('video')
                    video_url = 'https:' + video_tag.get('src')
                    data = urllib.request.urlopen(video_url)

                except Exception as e:
                    pprint(e)
                    return

                finally:
                    driver.quit()

                with open(filename, 'wb') as f:
                    f.write(data.read())

                cap = cv2.VideoCapture(filename)            # 動画を読み込む
                video_frame = cap.get(cv2.CAP_PROP_FRAME_COUNT)  # フレーム数を取得する
                video_fps = cap.get(cv2.CAP_PROP_FPS)           # FPS を取得する
                video_len_sec = video_frame / video_fps         # 長さ（秒）を計算する

                if video_len_sec > 140:
                    id_list.append(item['content_id'])
                    continue

                print(video_url)
                target = item
                break

        if target:
            break

    if not target:
        id_list = []
        return

    media_type = data.info()['Content-Type']
    total_bytes = data.info()['Content-Length']
    print(media_type, total_bytes, 'bytes')

    response = api.upload_video_init(total_bytes, media_type)

    if response.get('errors'):
        pprint(response)
        return

    media_id = response['media_id_string']

    # 5MB
    limit = 1048576 * 5

    data = urllib.request.urlopen(video_url)
    segment_index = 0
    while True:
        media = data.read(limit)

        if not media:
            break

        print(segment_index)
        api.upload_video_append(media_id, media, segment_index)
        segment_index += 1

    response = api.upload_video_final(media_id)

    if response.get('processing_info'):

        while True:
            check_after_secs = response['processing_info'].get('check_after_secs')

            if check_after_secs:
                sleep(check_after_secs)

            response = api.upload_video_status(media_id)

            state = response['processing_info'].get('state')
            if state == 'in_progress':
                continue

            elif state == 'succeeded':
                break

            else:
                pprint(response)
                return

    item_info = target['iteminfo']
    # maker = '【メーカー】' + item_info['maker'][0]['name'] if item_info.get('maker') else ''
    # series = '【シリーズ】' + item_info['series'][0]['name'] if item_info.get('series') else ''
    actress_list = [
        '#' + actress['name']
        for actress in item_info.get('actress', [])
        if isinstance(actress['id'], int)
    ]
    actress = '【女優】\n' + '\n'.join(actress_list) if actress_list else ''

    content_list = [
        target['title'],
        '',
        actress,
        '',
        '【ジャンル】\n' + '\n'.join(['#' + genre['name'] for genre in item_info['genre']]),
        '#140秒動画',
        '',
        '【詳細URL】' + target['affiliateURL'],
    ]

    status = '\n'.join(content_list)

    for i in range(4):
        if len(status) > 250:
            del content_list[2]
            status = '\n'.join(content_list)
            continue

        break

    response = api.post_tweet(status=status, media_ids=[media_id])

    if response.get('errors'):
        pprint(response)

    # twitter_tool.post_tweet(
    #     username=api.username,
    #     password=api.password,
    #     status=status,
    #     image_url_list=[image_url],
    # )

    id_list.append(target['content_id'])
    r.set(redis_key, json.dumps(list(set(id_list))), ex=None)
    print("SUCCESS: twitter:av_sommlier")


def post_av_actress():
    redis_key = 'twitter:av_actress'
    r = redis.from_url(REDIS_URL)
    rcache = r.get(redis_key)

    id_list = []
    if rcache:
        print("cache HIT!! %s" % (redis_key))
        id_list = json.loads(rcache.decode())

    tmp_id = None
    target_id = None

    hits = 100
    for i in range(10):
        response = dmm.search_items(keyword='単体作品', offset=i * hits + 1)

        for item in response['result']['items']:
            for actress in item['iteminfo'].get('actress', []):
                if not isinstance(actress['id'], int):
                    continue

                if actress['id'] not in id_list:
                    target_id = actress['id']
                    break

                if not tmp_id:
                    tmp_id = actress['id']

            if target_id:
                break

        if target_id:
            break

    if not target_id:
        target_id = tmp_id
        id_list = []

    response = dmm.search_actress(actress_id=target_id)

    if response['result']['result_count'] == 0:
        id_list.append(target_id)
        r.set(redis_key, json.dumps(list(set(id_list))), ex=None)
        return

    actress_info = response['result']['actress'][0]

    response = dmm.search_items(keyword='単体作品', article='actress', article_id=actress_info['id'])
    items = response['result']['items']

    api = get_twitter_api('av_actress')

    media_ids = []
    image_url_list = []
    for item in items:
        image_url = item['imageURL']['large']
        image_url_list.append(image_url)

        media = urllib.request.urlopen(image_url).read()
        response = api.upload_media(media)

        if response.get('errors'):
            pprint(response)
            return

        media_ids.append(response['media_id_string'])

        if len(image_url_list) >= 4:
            break

    ruby = '（%s）' % (actress_info['ruby']) if actress_info.get('ruby') else ''

    content_list = [
        '#%s %s' % (actress_info['name'], ruby),
        '',
    ]

    if actress_info.get('height'):
        content_list.append('【身長】' + actress_info['height'] + 'cm')

    if actress_info.get('cup'):
        content_list.append('【カップ】' + actress_info['cup'])

    if actress_info.get('bust') and actress_info.get('waist') and actress_info.get('hip'):
        content_list.append('【サイズ】B:%s W:%s H:%s' % (actress_info['bust'], actress_info['waist'], actress_info['hip']))

    if actress_info.get('birthday'):
        content_list.append('【誕生日】' + actress_info['birthday'])

    if actress_info.get('prefectures'):
        content_list.append('【出身地】' + actress_info['prefectures'])

    if actress_info.get('hobby'):
        content_list.append('【趣味】' + actress_info['hobby'])

    content_list.append('')
    content_list.append('【動画一覧】' + actress_info['listURL']['digital'])

    status = '\n'.join(content_list)

    for i in range(4):
        if len(status) > 270:
            del content_list[-3]
            status = '\n'.join(content_list)
            continue

        break

    # twitter_tool.post_tweet(
    #     username=api.username,
    #     password=api.password,
    #     status=status,
    #     image_url_list=image_url_list,
    # )

    response = api.post_tweet(status=status, media_ids=media_ids)

    if response.get('errors'):
        pprint(response)

    id_list.append(target_id)
    r.set(redis_key, json.dumps(list(set(id_list))), ex=None)
    print("SUCCESS: twitter:av_actress")


def search_and_retweet(account):
    api = get_twitter_api(account)
    response = api.get_account()

    if response.get('errors'):
        pprint(response)
        return

    redis_key = 'twitter:%s' % (account)
    r = redis.from_url(REDIS_URL)
    rcache = r.get(redis_key)

    id_list = []
    if rcache:
        print("cache HIT!! %s" % (redis_key))
        id_list = json.loads(rcache.decode())

    next_results = None
    tweet_list = []

    for _ in range(10):

        response = api.get_search_tweet(q=api.query, next_results=next_results)

        if response.get('errors'):
            pprint(response)
            break

        tweet_list += response['statuses']
        next_results = response['search_metadata'].get('next_results')

        if not next_results:
            break

    tweet_list = sorted(tweet_list, key=lambda k: k['retweet_count'], reverse=True)
    target = None

    for tweet in tweet_list:

        if tweet.get('retweeted_status'):
            continue

        if not target:
            target = tweet

        if tweet['id_str'] in id_list:
            continue

        target = tweet
        break

    if not target:
        return

    user = target['user']
    if not user.get('following') and not user.get('follow_request_sent') and not user.get('blocked_by'):
        response = api.post_follow(screen_name=user['screen_name'])

        if response.get('errors'):
            pprint(response)

        else:
            print("follow:", user['screen_name'])

    # 引用RTするツイートURL
    attachment_url = 'https://twitter.com/%s/status/%s' % (user['screen_name'], target['id_str'])

    # in_reply_to_status_id = None
    status = '今、人気のツイートはこちら！'
    if api.hashtag:
        # in_reply_to_status_id = target['id_str']
        now = datetime.now().strftime("%Y年%-m月%-d日(%a) %-H時00分")
        status = '%s\n%s の人気ツイート\n\n%s' % (now, api.hashtag, user['name'])

        length = 150
        status = status[:length] + ('...' if status[length:] else '')
        status = re.sub('(http|#|@)\S*\.\.\.', '...', status)
        print(len(status))

    # twitter_tool.search_and_retweet(
    #     username=api.username,
    #     password=api.password,
    #     status=status,
    #     tweet_path=attachment_url,
    # )

    response = api.post_tweet(
        status=status,
        attachment_url=attachment_url,
        # in_reply_to_status_id=in_reply_to_status_id
    )

    if response.get('errors'):
        pprint(response)

    id_list.append(target['id_str'])
    id_list = list(set(id_list))
    r.set(redis_key, json.dumps(id_list), ex=60 * 60 * 24 * 30)
    print("SUCCESS: twitter:", account)


def tweet_affiliate(account):

    redis_key = 'rakuten:%s' % (account)
    r = redis.from_url(REDIS_URL)
    rcache = r.get(redis_key)

    id_list = []
    if rcache:
        print("cache HIT!! %s" % (redis_key))
        id_list = json.loads(rcache.decode())

    api = get_twitter_api(account)

    target_item = None
    first_item = None
    for i in range(10):

        if not api.rakuten_query:
            response = rakuten.ranking_ichiba_item(page=i + 1)
        else:
            response = rakuten.search_ichiba_item(keyword=api.rakuten_query, page=i + 1)

        for item in response['Items']:

            if item['genreId'] in api.exclude_genre_id_list:
                continue

            if not first_item:
                first_item = item

            if item['itemCode'] in id_list:
                continue

            target_item = item
            break

        if target_item:
            break

    if not target_item:
        target_item = first_item
        id_list = []

    media_ids = []
    image_url_list = []
    for image_url in target_item['mediumImageUrls']:
        image_url = image_url.replace('128x128', '1000x1000')
        image_url_list.append(image_url)

        try:
            media = urllib.request.urlopen(image_url).read()

        except Exception as e:
            print(image_url)
            pprint(e)
            continue

        response = api.upload_media(media)

        if response.get('errors'):
            pprint(response)
            return

        media_ids.append(response['media_id_string'])

        if len(image_url_list) >= 4:
            break

    length = 90
    title = target_item.get('itemName', '') + '\n\n' + target_item.get('catchcopy', '')
    title = title[:length] + ('...' if title[length:] else '')

    content_list = [
        title,
        '',
        '【詳細URL】' + target_item.get('affiliateUrl'),
    ]

    status = '\n'.join(content_list)

    # twitter_tool.post_tweet(
    #     username=api.username,
    #     password=api.password,
    #     status=status,
    #     image_url_list=image_url_list,
    # )

    response = api.post_tweet(status=status, media_ids=media_ids)

    if response.get('errors'):
        pprint(response)

    id_list.append(target_item['itemCode'])
    r.set(redis_key, json.dumps(id_list), ex=None)

    print("SUCCESS: tweet_affiliate", account)


def retweet_user(account, screen_name=None):
    api = get_twitter_api(account)

    if not api.retweet_list:
        return

    if not screen_name:
        screen_name = choice(api.retweet_list)

    response = api.get_user_timeline(screen_name)
    tweet_list = sorted(response, key=lambda k: k.get('favorite_count', 0), reverse=True)

    target = None
    for tweet in tweet_list:

        if tweet.get('retweeted'):
            continue

        target = tweet
        break

    if not target:
        return

    response = api.post_retweet(target['id_str'])
    if response.get('errors'):
        pprint(response)

    print("SUCCESS: retweet_user", account)


def favorite_tweet(account):
    api = get_twitter_api(account)

    response = api.get_trend()
    trends = response[0]['trends']
    trend = choice(trends)
    print(trend['name'])

    response = api.get_search_tweet(q=trend['name'], result_type='recent')
    tweet_list = response['statuses']
    target_list = list(filter(lambda x: x.get('favorited') is False and x.get('lang') == 'ja', tweet_list))

    for i, target in enumerate(target_list[:5]):
        print(i)
        response = api.post_favorite(target['id_str'])

        if response.get('errors'):
            pprint(response)
            return

    print("SUCCESS: favorite_tweet", account)


def tweet_tiktok():
    account = 'tiktok'
    api = get_twitter_api(account)

    redis_key = 'tweet_tiktok'
    r = redis.from_url(REDIS_URL)
    rcache = r.get(redis_key)

    start_follower = None
    if rcache:
        print("cache HIT!! %s" % (redis_key))
        start_follower = json.loads(rcache.decode())

    helper_firestore.initialize_firebase()
    ref = firestore.client().collection('users')

    query = ref.order_by('follower_count', direction=firestore.Query.DESCENDING)

    if start_follower:
        query = query.start_after({'follower_count': start_follower})

    docs = query.limit(1).get()
    data = list(docs)[0].to_dict()

    pprint(data)

    content_list = []

    if data.get('custom_verify'):
        content_list.append('【%s】' % (data['custom_verify']))

    content_list.append(data.get('nickname', ''))

    _follower = data['follower_count']
    follower = round(_follower, -len(str(_follower)) + 2)
    follower = "{:,d}".format(follower)
    content_list.append('ファン： %s人' % (follower))

    if data.get('signature'):
        content_list.append('\n' + str(data['signature']) + '\n')

    # if data.get('twitter_name'):
    #     content_list.append('【Twitter】@%s' % (data['twitter_name']))

    content_list.append('【TikTok】%s' % (data['share_url'].replace('/?', '')))

    image_url_list = []
    if data.get('avatar_medium'):
        image_url_list.append(data['avatar_medium'])

    media_ids = []
    for image_url in image_url_list:
        try:
            media = urllib.request.urlopen(image_url).read()

        except Exception as e:
            print(image_url)
            pprint(e)
            continue

        response = api.upload_media(media)

        if response.get('errors'):
            pprint(response)
            return

        media_ids.append(response['media_id_string'])

        if len(media_ids) >= 4:
            break

    status = '\n'.join(content_list)
    print(status)
    print(len(status))

    # twitter_tool.post_tweet(
    #     username=api.username,
    #     password=api.password,
    #     status=status,
    #     image_url_list=image_url_list,
    # )

    response = api.post_tweet(status=status, media_ids=media_ids)

    if response.get('errors'):
        pprint(response)

    start_follower = data['follower_count']
    r.set(redis_key, json.dumps(start_follower), ex=60 * 60 * 24 * 30)

    print("SUCCESS: tweet_tiktok", account)


def tweet_tiktok_video():
    account = 'tiktok'
    api = get_twitter_api(account)

    redis_key = 'tweet_tiktok_video'
    r = redis.from_url(REDIS_URL)
    rcache = r.get(redis_key)

    id_list = []
    if rcache:
        print("cache HIT!! %s" % (redis_key))
        id_list = json.loads(rcache.decode())

    # 1週間前
    # filter_time = int(time()) - (60 * 60 * 24 * 7)

    helper_firestore.initialize_firebase()
    ref = firestore.client().collection('videos')

    # .where('create_time', '>', filter_time) \
    # .order_by('create_time') \

    last_data = None
    target = None
    tmp = None
    for _ in range(50):

        query = ref \
            .order_by('create_time') \
            .order_by('digg_count', direction=firestore.Query.DESCENDING)

        if last_data:
            query = query.start_after({
                'create_time': last_data.get('create_time'),
                'digg_count': last_data.get('digg_count'),
            })

        docs = query.limit(10).get()
        results = [doc.to_dict() for doc in docs]

        for data in results:

            if not tmp:
                tmp = data

            if data.get('aweme_id') in id_list:
                continue

            target = data
            break

        if target:
            break

        last_data = results[-1]

    if not target:
        target = tmp
        id_list = []

    media_id = upload_video(api, video_url=target['download_url'])

    if not media_id:
        return

    content_list = []

    content_list.append(target.get('nickname'))
    content_list.append(target.get('desc', ''))
    content_list.append('\n【詳細URL】%s' % (target.get('share_url')))

    status = '\n'.join(content_list)
    response = api.post_tweet(status=status, media_ids=[media_id])

    if response.get('errors'):
        pprint(response)

    id_list.append(target.get('aweme_id'))
    r.set(redis_key, json.dumps(id_list), ex=60 * 60 * 24 * 30)

    print("SUCCESS: tweet_tiktok_video", account)


def follow_users_by_retweet(account):

    api = get_twitter_api(account)
    response = api.get_account()

    if response.get('errors'):
        pprint(response)
        return

    response = api.get_home_timeline()
    if isinstance(response, dict) and response.get('errors'):
        pprint(response)
        return

    retweeter_count = 0
    tweet_id_list = set()

    tweet_list = sorted(response, key=lambda k: k.get('retweet_count', 0), reverse=True)
    for tweet in tweet_list:

        if tweet.get('retweet_count', 0) <= 1:
            continue

        if tweet.get('lang') not in ['ja']:
            continue

        retweeter_count += tweet['retweet_count']
        tweet_id = tweet['id_str']
        if tweet.get('retweeted_status'):
            tweet_id = tweet['retweeted_status']['id_str']

        tweet_id_list.add(tweet_id)

        if retweeter_count > 5:
            break

    user_id_list = set()
    for tweet_id in tweet_id_list:
        response = api.get_retweet_user(tweet_id=tweet_id)

        if isinstance(response, dict) and response.get('errors'):
            pprint(response)
            continue

        tweet_list = sorted(response, key=lambda k: k['user'].get('friends_count', 0), reverse=True)
        for tweet in tweet_list:
            user = tweet['user']

            if user.get('following') or user.get('follow_request_sent') or user.get('blocked_by'):
                continue

            if user.get('lang') not in ['ja']:
                continue

            user_id_list.add(user['screen_name'])

    for num, user_id in enumerate(list(user_id_list)[:3], 1):
        response = api.post_follow(screen_name=user_id)

        if response.get('errors'):
            pprint(response)
            break

        print("SUCCESS:%s follow:%s" % (num, user_id))

        sleep_time = randint(1, 10)
        print("sleep_time:", sleep_time)
        sleep(sleep_time)

    print("SUCCESS: twitter:follow_users_by_retweet %s" % (account))


def follow_users_by_follower(account):
    api = get_twitter_api(account)
    response = api.get_account()

    if response.get('errors'):
        pprint(response)
        return

    followers_count = response['followers_count']
    if followers_count == 0:
        return

    friends_count = response['friends_count']
    if friends_count >= 4950 and friends_count - followers_count > 0:
        return

    account_id = response['id_str']
    response = api.get_followers(user_id=account_id)

    if response.get('errors'):
        pprint(response)
        return

    follower_id_list = [user['id_str'] for user in response['users']]
    shuffle(follower_id_list)

    user_list = set()
    for follower_id in follower_id_list:
        response = api.get_followers(user_id=follower_id)
        users = sorted(response['users'], key=lambda k: k['friends_count'], reverse=True)

        for user in users:

            if user.get('following') or user.get('follow_request_sent') or user.get('blocked_by'):
                continue

            if user['id_str'] == account_id:
                continue

            if user.get('lang') not in ['ja']:
                continue

            user_list.add(user['screen_name'])

        if len(user_list) > 10:
            break

    user_list = list(user_list)
    limit = 3

    # twitter_tool.follow_users(
    #     username=api.username,
    #     password=api.password,
    #     user_list=user_list[:limit],
    # )

    for num, screen_name in enumerate(list(user_list)[:limit], 1):
        response = api.post_follow(screen_name=screen_name)

        if response.get('errors'):
            pprint(response)
            break

        print("SUCCESS:%s follow:%s" % (num, screen_name))

        if num >= limit:
            break

        sleep_time = randint(1, 10)
        print("sleep_time:", sleep_time)
        sleep(sleep_time)

    print("SUCCESS: twitter:follow_users_by_follower %s" % (account))


def follow_target_user(account):
    api = get_twitter_api(account)

    if not api.target_list:
        return

    response = api.get_account()

    if response.get('errors'):
        pprint(response)
        return

    friends_count = response['friends_count']
    followers_count = response['followers_count']
    if friends_count >= 4950 and friends_count - followers_count > 0:
        return

    account_id = response['id_str']
    LIMIT = 3

    screen_name = choice(api.target_list)
    print("target_user:", screen_name)
    response = api.get_followers(screen_name=screen_name)
    users = sorted(response['users'], key=lambda k: k['friends_count'], reverse=True)

    user_list = set()
    for user in users:

        if user.get('following') or user.get('follow_request_sent') or user.get('blocked_by'):
            continue

        if user['id_str'] == account_id:
            continue

        if user.get('lang') not in ['ja']:
            continue

        user_list.add(user['screen_name'])

        if len(user_list) > LIMIT:
            break

    user_list = list(user_list)

    # twitter_tool.follow_users(
    #     username=api.username,
    #     password=api.password,
    #     user_list=user_list[:LIMIT],
    # )

    for num, screen_name in enumerate(list(user_list)[:LIMIT], 1):
        response = api.post_follow(screen_name=screen_name)

        if response.get('errors'):
            pprint(response)
            break

        print("SUCCESS:%s follow:%s" % (num, screen_name))

        if num >= LIMIT:
            break

        sleep_time = randint(1, 10)
        print("sleep_time:", sleep_time)
        sleep(sleep_time)

    print("SUCCESS: twitter:follow_target_user %s" % (account))


def remove_follow(account):

    api = get_twitter_api(account)
    response = api.get_account()

    if response.get('errors'):
        pprint(response)
        return

    if response['friends_count'] < 100:
        return

    account_id = response['id_str']

    user_list = []
    cursor = -1

    for _ in range(10):

        response = api.get_followings(
            user_id=account_id,
            cursor=cursor,
            count=100,
        )

        if response.get('errors'):
            pprint(response)
            break

        cursor = response.get('next_cursor_str')
        print("cursor:", cursor)
        following_id_list = [user['id_str'] for user in response['users']]

        response = api.get_friendships(user_id=','.join(following_id_list))

        user_list += [
            user['screen_name']
            for user in response
            if "followed_by" not in user['connections']
        ]

        if not cursor or cursor == "0":
            break

    user_list = list(reversed(user_list))
    limit = randint(3, 6)

    # twitter_tool.follow_users(
    #     username=api.username,
    #     password=api.password,
    #     user_list=user_list[:limit],
    # )

    for num, screen_name in enumerate(user_list[:limit], 1):
        response = api.post_unfollow(screen_name=screen_name)

        if response.get('errors'):
            pprint(response)
            break

        print("SUCCESS:%s unfollow:%s" % (num, screen_name))

        if num >= limit:
            break

        sleep_time = randint(5, 15)
        print("sleep_time:", sleep_time)
        sleep(sleep_time)

    print("SUCCESS: twitter:remove_follow %s" % (account))


def get_twitter_api(account):
    username = ''
    password = ''
    hashtag = ''
    query = ''
    rakuten_query = ''
    exclude_genre_id_list = []
    target_list = []
    retweet_list = []

    if account == 'av_sommlier':
        access_token = TWITTER_AV_SOMMLIER_ACCESS_TOKEN
        secret = TWITTER_AV_SOMMLIER_SECRET
        username = 'av_video_bot'
        password = TWITTER_PASSWORD_A
        target_list = ['fanza_sns']
        retweet_list = ['av_actress_bot']

    elif account == 'av_actress':
        access_token = TWITTER_AV_ACTRESS_ACCESS_TOKEN
        secret = TWITTER_AV_ACTRESS_SECRET
        username = 'av_actress_bot'
        password = TWITTER_PASSWORD_A
        target_list = ['fanza_sns']
        rakuten_query = '精力'
        retweet_list = ['av_video_bot']

    elif account == "github":
        access_token = TWITTER_GITHUB_ACCESS_TOKEN
        secret = TWITTER_GITHUB_SECRET
        username = 'git_hub_status'
        password = TWITTER_PASSWORD_A
        target_list = ['github', 'githubstatus']

    elif account == 'vtuber':
        access_token = TWITTER_VTUBER_ACCESS_TOKEN
        secret = TWITTER_VTUBER_SECRET
        username = 'kizunaAI_images'
        password = TWITTER_PASSWORD_B

        words = [
            "vtuber"
            "バーチャルYouTuber",
            "KizunaAI",
            "キズナアイ",
            "輝夜月",
            "電脳少女シロ",
            "SiroArt",
            "ミライアカリ",
            "のじゃロリ狐娘",
            "Nora_Cat",
            "のらきゃっと",
            "みとあーと",
            "猫宮ひなた",
            "HinataCat",
            "soraArt",
            "ばあちゃる",
            "鳩羽つぐ",
            '名取さな',
            'にじさんじ',
        ]

        hashtag = '#バーチャルYouTuber'
        query = '(%s) (filter:images OR filter:videos) min_retweets:50' % (' OR '.join(words))
        rakuten_query = 'キズナアイ 電脳少女シロ 輝夜月 ミライアカリ 月ノ美兎 猫宮ひなた にじさんじ'
        target_list = ['aichan_nel', 'SIROyoutuber', 'MiraiAkari_prj', '_KaguyaLuna', 'kizuna_ai_scn']

    elif account == 'splatoon':
        access_token = TWITTER_SPLATTON_ACCESS_TOKEN
        secret = TWITTER_SPLATOON_SECRET
        username = 'splatoon2_ninki'
        password = TWITTER_PASSWORD_B

        hashtag = '#Splatoon2'
        query = '(#Splatoon2) (filter:images OR filter:videos) min_retweets:10'
        rakuten_query = 'スプラトゥーン'
        exclude_genre_id_list = ['566404', '566406']
        target_list = ['SplatoonJP']

    elif account == 'smash_bros':
        access_token = TWITTER_SMASH_BROS_ACCESS_TOKEN
        secret = TWITTER_SMASH_BROS_SECRET
        username = 'smash_bros_sp'
        password = TWITTER_PASSWORD_B

        hashtag = '#スマブラSP'
        query = '(#スマブラSP OR #SmashBrosSP) (filter:images OR filter:videos) min_retweets:10'
        rakuten_query = 'カービィ'
        exclude_genre_id_list = ['566404', '566406', '566420']
        target_list = ['SmashBrosJP']

    elif account == 'tiktok':
        access_token = TWITTER_TIKTOK_ACCESS_TOKEN
        secret = TWITTER_TIKTOK_SECRET
        username = 'tiktok_rank_jp'
        password = TWITTER_PASSWORD_A

        hashtag = '#TikTok'
        query = '#TikTok filter:videos min_retweets:10'
        rakuten_query = "コスプレ"
        target_list = ['tiktok_japan']

    elif account == 'hypnosismic':
        access_token = TWITTER_HYPNOSISMIC_ACCESS_TOKEN
        secret = TWITTER_HYPNOSISMIC_SECRET
        username = 'bot_hypnosismic'
        password = TWITTER_PASSWORD_B
        hashtag = '#ヒプノシスマイク'
        query = '(ヒプノシスマイク OR ヒプマイ) (filter:images OR filter:videos) min_retweets:10'
        rakuten_query = 'ヒプノシスマイク'
        target_list = ['hypnosismic']

    elif account == 'rakuten_rank':
        access_token = TWITTER_RAKUTEN_RANK_ACCESS_TOKEN
        secret = TWITTER_RAKUTEN_RANK_SECRET
        username = '_rakuten_rank'
        password = TWITTER_PASSWORD_A
        target_list = ['RakutenJP']

    else:
        print("NO MATCH")

    return TwitterApi(
        access_token,
        secret,
        username=username,
        password=password,
        hashtag=hashtag,
        query=query,
        rakuten_query=rakuten_query,
        exclude_genre_id_list=exclude_genre_id_list,
        target_list=target_list,
        retweet_list=retweet_list,
    )


def upload_video(api, video_url):
    data = urllib.request.urlopen(video_url)
    media_type = data.info()['Content-Type']
    total_bytes = data.info()['Content-Length']
    response = api.upload_video_init(total_bytes, media_type)

    if response.get('errors'):
        pprint(response)
        return None

    media_id = response['media_id_string']

    # 5MB
    limit = 1048576 * 5

    data = urllib.request.urlopen(video_url)
    segment_index = 0
    while True:
        media = data.read(limit)

        if not media:
            break

        print(segment_index)
        api.upload_video_append(media_id, media, segment_index)
        segment_index += 1

    response = api.upload_video_final(media_id)

    if response.get('processing_info'):

        while True:
            check_after_secs = response['processing_info'].get('check_after_secs')

            if check_after_secs:
                sleep(check_after_secs)

            response = api.upload_video_status(media_id)

            state = response['processing_info'].get('state')
            if state == 'in_progress':
                continue

            elif state == 'succeeded':
                break

            else:
                pprint(response)
                return None

    return media_id


def get_driver():
    options = ChromeOptions()
    options.binary_location = GOOGLE_CHROME_PATH
    options.add_argument('--headless')
    options.add_argument("start-maximized")  # open Browser in maximized mode
    options.add_argument("disable-infobars")  # disabling infobars
    options.add_argument("--disable-extensions")  # disabling extensions
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")  # overcome limited resource problem

    driver = Chrome(executable_path=DRIVER_PATH, chrome_options=options)
    driver.set_page_load_timeout(10)
    driver.set_script_timeout(10)
    driver.implicitly_wait(10)

    return driver
