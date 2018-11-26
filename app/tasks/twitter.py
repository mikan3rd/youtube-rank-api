import json
import re
import urllib.request
from datetime import datetime
from pprint import pprint
from random import choice, randint, shuffle
from time import sleep

import redis
from firebase_admin import firestore
from settings import (
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
from app.tasks import twitter_tool


def post_av_sommlier():

    redis_key = 'twitter:av_sommlier'
    r = redis.from_url(REDIS_URL)
    rcache = r.get(redis_key)

    title_list = []
    if rcache:
        print("cache HIT!! %s" % (redis_key))
        title_list = json.loads(rcache.decode())

    response = dmm.search_items()
    items = response['result']['items']

    target_index = 0
    for index, item in enumerate(items):

        if item['content_id'] in title_list:
            continue

        target_index = index
        break

    else:
        title_list = []

    target = items[target_index]

    api = get_twitter_api('av_sommlier')

    image_url = target['imageURL']['large']
    # media = urllib.request.urlopen(image_url).read()
    # response = api.upload_media(media)

    # if response.get('errors'):
    #     pprint(response)
    #     return

    # media_id = response['media_id_string']    # type: ignore

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
        '',
        '【詳細URL】' + target['affiliateURL'],
    ]

    status = '\n'.join(content_list)

    for i in range(2):
        if len(status) > 260:
            del content_list[2]
            status = '\n'.join(content_list)
            continue

        break

    twitter_tool.post_tweet(
        username=api.username,
        password=api.password,
        status=status,
        image_url_list=[image_url],
    )

    # response = api.post_tweet(status=status, media_ids=[media_id])

    # if response.get('errors'):
    #     pprint(response)

    title_list.append(target['content_id'])
    r.set(redis_key, json.dumps(list(set(title_list))), ex=None)
    print("SUCCESS: twitter:av_sommlier")


def post_av_actress():
    redis_key = 'twitter:av_actress'
    r = redis.from_url(REDIS_URL)
    rcache = r.get(redis_key)

    id_list = []
    if rcache:
        print("cache HIT!! %s" % (redis_key))
        id_list = json.loads(rcache.decode())

    response = dmm.search_items(keyword='単体作品')

    tmp_id = None
    target_id = None
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

    if not target_id:
        target_id = tmp_id
        id_list = []

    response = dmm.search_actress(actress_id=target_id)
    actress_info = response['result']['actress'][0]

    keyword = '%s 単体作品' % (actress_info['name'])
    response = dmm.search_items(keyword=keyword)
    items = response['result']['items']

    api = get_twitter_api('av_actress')

    media_ids = []
    image_url_list = []
    for item in items:
        image_url = item['imageURL']['large']
        image_url_list.append(image_url)

        # media = urllib.request.urlopen(image_url).read()
        # response = api.upload_media(media)

        # if response.get('errors'):
        #     pprint(response)
        #     return

        # media_ids.append(response['media_id_string'])

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

    twitter_tool.post_tweet(
        username=api.username,
        password=api.password,
        status=status,
        image_url_list=image_url_list,
    )
    # response = api.post_tweet(status=status, media_ids=media_ids)

    # if response.get('errors'):
    #     pprint(response)

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

    response = api.get_search_tweet(q=api.query)

    if response.get('errors'):
        pprint(response)
        return

    tweet_list = response['statuses']
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

    in_reply_to_status_id = None
    status = '今、人気のツイートはこちら！'
    if api.hashtag:
        in_reply_to_status_id = target['id_str']
        user = target['user']
        now = datetime.now().strftime("%Y年%-m月%-d日(%a) %-H時00分")

        status = '%s\n%s の人気ツイート\n\n@%s %s\n%s' \
            % (now, api.hashtag, user['screen_name'], user['name'], user['description'])

        length = 150
        status = status[:length] + ('...' if status[length:] else '')
        status = re.sub('(http|#|@)\S*\.\.\.', '...', status)
        print(len(status))

    attachment_url = 'https://twitter.com/%s/status/%s' % (target['user']['screen_name'], target['id_str'])

    twitter_tool.search_and_retweet(
        username=api.username,
        password=api.password,
        status=status,
        tweet_path=attachment_url,
    )

    # response = api.post_tweet(
    #     status=status,
    #     attachment_url=attachment_url,
    #     # in_reply_to_status_id=in_reply_to_status_id
    # )

    # if response.get('errors'):
    #     pprint(response)

    id_list.append(target['id_str'])
    id_list = list(set(id_list))
    r.set(redis_key, json.dumps(id_list), ex=None)
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
    response = rakuten.search_ichiba_item(keyword=api.rakuten_query)

    target_item = None
    for item in response['Items']:

        if item['genreId'] in api.exclude_genre_id_list:
            continue

        if not target_item:
            target_item = item

        if item['itemCode'] in id_list:
            continue

        target_item = item
        break

    if not target_item:
        target_item = response['Items'][0]
        id_list = []

    media_ids = []
    image_url_list = []
    for image_url in target_item['mediumImageUrls']:
        image_url = image_url.replace('128x128', '1000x1000')
        image_url_list.append(image_url)
        # media = urllib.request.urlopen(image_url).read()
        # response = api.upload_media(media)

        # if response.get('errors'):
        #     pprint(response)
        #     return

        # media_ids.append(response['media_id_string'])

        if len(image_url_list) >= 4:
            break

    length = 90
    title = target_item.get('itemName')
    title = title[:length] + ('...' if title[length:] else '')

    content_list = [
        target_item.get('catchcopy'),
        title,
        '',
        '【詳細URL】' + target_item.get('affiliateUrl'),
    ]

    status = '\n'.join(content_list)

    twitter_tool.post_tweet(
        username=api.username,
        password=api.password,
        status=status,
        image_url_list=image_url_list,
    )

    # response = api.post_tweet(status=status, media_ids=media_ids)

    # if response.get('errors'):
    #     pprint(response)

    id_list.append(target_item['itemCode'])
    r.set(redis_key, json.dumps(id_list), ex=None)

    print("SUCCESS: tweet_affiliate", account)


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
        content_list.append('\n' + data['signature'] + '\n')

    if data.get('twitter_name'):
        content_list.append('【Twitter】@%s' % (data['twitter_name']))

    content_list.append('【TikTok】%s' % (data['share_url']))

    image_url_list = []
    if data.get('avatar_medium'):
        image_url_list.append(data['avatar_medium'])

    status = '\n'.join(content_list)
    print(status)
    print(len(status))

    twitter_tool.post_tweet(
        username=api.username,
        password=api.password,
        status=status,
        image_url_list=image_url_list,
    )

    start_follower = data['follower_count']
    r.set(redis_key, json.dumps(start_follower), ex=None)

    print("SUCCESS: tweet_tiktok", account)


def follow_users_by_retweet(account):

    api = get_twitter_api(account)
    response = api.get_account()

    if response.get('errors'):
        pprint(response)
        return

    if response['followers_count'] >= 5:
        return

    response = api.get_home_timeline()
    if isinstance(response, dict) and response.get('errors'):
        pprint(response)
        return

    retweeter_count = 0
    tweet_id_list = set()
    for tweet in response:

        if tweet.get('retweet_count', 0) <= 1:
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

        for tweet in response:
            user = tweet['user']

            if user.get('following') or user.get('follow_request_sent') or user.get('blocked_by'):
                continue

            user_id_list.add(user['id_str'])

    for num, user_id in enumerate(list(user_id_list)[:5], 1):
        response = api.post_follow(user_id=user_id)

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

        for user in response['users']:
            if user.get('following') or user.get('follow_request_sent') or user.get('blocked_by'):
                continue

            if user['id_str'] == account_id:
                continue

            if followers_count > 1000 and user.get('lang') not in ['en', 'ja']:
                continue

            user_list.add(user['screen_name'])

        if len(user_list) > 10:
            break

    user_list = list(user_list)
    limit = randint(3, 6)

    twitter_tool.follow_users(
        username=api.username,
        password=api.password,
        user_list=user_list[:limit],
    )

    # for num, screen_name in enumerate(list(user_list)[:limit], 1):
    #     response = api.post_follow(screen_name=screen_name)

    #     if response.get('errors'):
    #         pprint(response)
    #         break

    #     print("SUCCESS:%s follow:%s" % (num, screen_name))

    #     if num >= limit:
    #         break

    #     sleep_time = randint(1, 10)
    #     print("sleep_time:", sleep_time)
    #     sleep(sleep_time)

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
    LIMIT = randint(3, 5)

    screen_name = choice(api.target_list)
    print("target_user:", screen_name)
    response = api.get_followers(screen_name=screen_name)

    user_list = set()
    for user in response['users']:
        if user.get('following') or user.get('follow_request_sent') or user.get('blocked_by'):
            continue

        if user['id_str'] == account_id:
            continue

        user_list.add(user['screen_name'])

        if len(user_list) > LIMIT:
            break

    user_list = list(user_list)
    twitter_tool.follow_users(
        username=api.username,
        password=api.password,
        user_list=user_list[:LIMIT],
    )

    # for num, screen_name in enumerate(list(user_list)[:LIMIT], 1):
    #     response = api.post_follow(screen_name=screen_name)

    #     if response.get('errors'):
    #         pprint(response)
    #         break

    #     print("SUCCESS:%s follow:%s" % (num, screen_name))

    #     if num >= LIMIT:
    #         break

    #     sleep_time = randint(1, 10)
    #     print("sleep_time:", sleep_time)
    #     sleep(sleep_time)

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
    limit = randint(3, 5)

    twitter_tool.follow_users(
        username=api.username,
        password=api.password,
        user_list=user_list[:limit],
    )

    # for num, screen_name in enumerate(user_list, 1):
    #     response = api.post_unfollow(screen_name=screen_name)

    #     if response.get('errors'):
    #         pprint(response)
    #         break

    #     print("SUCCESS:%s unfollow:%s" % (num, screen_name))

    #     if num >= 3:
    #         break

    #     sleep_time = randint(10, 60)
    #     print("sleep_time:", sleep_time)
    #     sleep(sleep_time)

    print("SUCCESS: twitter:remove_follow %s" % (account))


def get_twitter_api(account):
    username = ''
    password = ''
    hashtag = ''
    query = ''
    rakuten_query = ''
    exclude_genre_id_list = []
    target_list = []

    if account == 'av_sommlier':
        access_token = TWITTER_AV_SOMMLIER_ACCESS_TOKEN
        secret = TWITTER_AV_SOMMLIER_SECRET
        username = 'av_movie_bot'
        password = TWITTER_PASSWORD_A
        target_list = ['fanza_sns']

    elif account == 'av_actress':
        access_token = TWITTER_AV_ACTRESS_ACCESS_TOKEN
        secret = TWITTER_AV_ACTRESS_SECRET
        username = 'av_actress_bot'
        password = TWITTER_PASSWORD_A
        target_list = ['fanza_sns']

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
            "バーチャルのじゃロリ狐娘youtuberおじさん",
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
        target_list = ['aichan_nel', 'SIROyoutuber', 'MiraiAkari_prj', '_KaguyaLuna']

    elif account == 'splatoon':
        access_token = TWITTER_SPLATTON_ACCESS_TOKEN
        secret = TWITTER_SPLATOON_SECRET
        username = 'splatoon2_ninki'
        password = TWITTER_PASSWORD_B

        hashtag = '#Splatoon2'
        query = '#Splatoon2 filter:videos min_retweets:10'
        rakuten_query = 'スプラトゥーン'
        exclude_genre_id_list = ['566404', '566406']
        target_list = ['SplatoonJP']

    elif account == 'smash_bros':
        access_token = TWITTER_SMASH_BROS_ACCESS_TOKEN
        secret = TWITTER_SMASH_BROS_SECRET
        username = 'smash_bros_sp'
        password = TWITTER_PASSWORD_B

        hashtag = '#スマブラSP'
        query = '(スマブラSP) (filter:images OR filter:videos) min_retweets:10'
        rakuten_query = 'スマッシュブラザーズ'
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
    )
