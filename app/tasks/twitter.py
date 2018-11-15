import json
import urllib.request
from pprint import pprint
from random import randint, shuffle
from time import sleep

import redis
from settings import (
    REDIS_URL,
    TWITTER_AV_ACTRESS_ACCESS_TOKEN,
    TWITTER_AV_ACTRESS_SECRET,
    TWITTER_AV_SOMMLIER_ACCESS_TOKEN,
    TWITTER_AV_SOMMLIER_SECRET,
    TWITTER_SMASH_BROS_ACCESS_TOKEN,
    TWITTER_SMASH_BROS_SECRET,
    TWITTER_GITHUB_ACCESS_TOKEN,
    TWITTER_GITHUB_SECRET,
    TWITTER_VTUBER_ACCESS_TOKEN,
    TWITTER_VTUBER_SECRET,
    TWITTER_SPLATTON_ACCESS_TOKEN,
    TWITTER_SPLATOON_SECRET,
)

from app.server.helpers import dmm, rakuten
from app.server.helpers.twitter import TwitterApi


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

    api = TwitterApi(TWITTER_AV_SOMMLIER_ACCESS_TOKEN, TWITTER_AV_SOMMLIER_SECRET)

    media = urllib.request.urlopen(target['imageURL']['large']).read()
    response = api.upload_media(media)

    if response.get('errors'):
        pprint(response)
        return

    media_id = response['media_id_string']    # type: ignore

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

    print(status)
    response = api.post_tweet(status=status, media_ids=[media_id])

    if response.get('errors'):
        pprint(response)

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

    response = dmm.search_items()

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

    api = TwitterApi(TWITTER_AV_ACTRESS_ACCESS_TOKEN, TWITTER_AV_ACTRESS_SECRET)

    media_ids = []
    for item in items:
        media = urllib.request.urlopen(item['imageURL']['large']).read()
        response = api.upload_media(media)

        if response.get('errors'):
            pprint(response)
            return

        media_ids.append(response['media_id_string'])

        if len(media_ids) >= 4:
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

    print(status)
    response = api.post_tweet(status=status, media_ids=media_ids)

    if response.get('errors'):
        pprint(response)

    id_list.append(target_id)
    r.set(redis_key, json.dumps(list(set(id_list))), ex=None)
    print("SUCCESS: twitter:av_actress")


def search_and_retweet(account, query):
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

    response = api.get_search_tweet(q=query)

    if response.get('errors'):
        pprint(response)
        return

    tweet_list = response['statuses']
    tweet_list = sorted(tweet_list, key=lambda k: k['retweet_count'], reverse=True)
    print(len(tweet_list))

    target_id = None
    for tweet in tweet_list:

        if tweet.get('retweeted'):
            continue

        if tweet['id_str'] in id_list:
            continue

        target_id = tweet['id_str']
        break

    if not target_id:
        print(account, "nothing to tweet")
        return

    response = api.post_retweet(target_id)

    if response.get('errors'):
        pprint(response)
        return

    id_list.append(target_id)
    r.set(redis_key, json.dumps(list(set(id_list))), ex=None)
    print("SUCCESS: twitter:", account)

    if len(id_list) % 10 == 0:
        tweet_affiliate(account)


def tweet_affiliate(account):
    sleep(10)

    if account == 'smash_bros':
        keyword = 'スマッシュブラザーズ'

    elif account == 'vtuber':
        keyword = 'キズナアイ'

    elif account == 'splatoon':
        keyword = 'スプラトゥーン'

    else:
        return

    response = rakuten.search_ichiba_item(keyword=keyword)
    targtet_item = response['Items'][0]

    content_list = [
        targtet_item.get('itemName'),
        targtet_item.get('affiliateUrl')
    ]

    status = '\n'.join(content_list)

    api = get_twitter_api(account)
    response = api.post_tweet(status=status)

    if response.get('errors'):
        pprint(response)

    print("SUCCESS: tweet_affiliate", account)


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

    print("tweet_id_list:")
    pprint(tweet_id_list)

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

    # print("user_id_list:")
    # pprint(user_id_list)
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
    if friends_count >= 4990 and friends_count - followers_count > 0:
        return

    account_id = response['id_str']
    response = api.get_followers(user_id=account_id)

    if response.get('errors'):
        pprint(response)
        return

    follower_id_list = [user['id_str'] for user in response['users']]
    shuffle(follower_id_list)

    user_id_list = set()
    for follower_id in follower_id_list:
        response = api.get_followers(user_id=follower_id)

        for user in response['users']:
            if user.get('following') or user.get('follow_request_sent') or user.get('blocked_by'):
                continue

            if user['id_str'] == account_id:
                continue

            user_id_list.add(user['screen_name'])

        if len(user_id_list) > 10:
            break

    # print("user_id_list:")
    # pprint(user_id_list)
    for num, screen_name in enumerate(list(user_id_list)[:10], 1):
        response = api.post_follow(screen_name=screen_name)

        if response.get('errors'):
            pprint(response)
            break

        print("SUCCESS:%s follow:%s" % (num, screen_name))

        if num >= 10:
            break

        sleep_time = randint(1, 10)
        print("sleep_time:", sleep_time)
        sleep(sleep_time)

    print("SUCCESS: twitter:follow_users_by_follower %s" % (account))


def remove_follow(account):

    api = get_twitter_api(account)
    response = api.get_account()

    if response.get('errors'):
        pprint(response)
        return

    if response['friends_count'] < 100:
        return

    account_id = response['id_str']

    user_id_list = []
    cursor = -1

    for _ in range(15):

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

        user_id_list += [
            user['screen_name']
            for user in response
            if "followed_by" not in user['connections']
        ]

        if not cursor or cursor == "0":
            break

    user_id_list = reversed(user_id_list)
    for num, screen_name in enumerate(user_id_list, 1):
        response = api.post_unfollow(screen_name=screen_name)

        if response.get('errors'):
            pprint(response)
            break

        print("SUCCESS:%s unfollow:%s" % (num, screen_name))

        if num >= 4:
            break

        sleep_time = randint(10, 70)
        print("sleep_time:", sleep_time)
        sleep(sleep_time)

    print("SUCCESS: twitter:remove_follow %s" % (account))


def get_twitter_api(account):
    if account == 'av_sommlier':
        access_token = TWITTER_AV_SOMMLIER_ACCESS_TOKEN
        secret = TWITTER_AV_SOMMLIER_SECRET

    elif account == 'av_actress':
        access_token = TWITTER_AV_ACTRESS_ACCESS_TOKEN
        secret = TWITTER_AV_ACTRESS_SECRET

    elif account == 'smash_bros':
        access_token = TWITTER_SMASH_BROS_ACCESS_TOKEN
        secret = TWITTER_SMASH_BROS_SECRET

    elif account == "github":
        access_token = TWITTER_GITHUB_ACCESS_TOKEN
        secret = TWITTER_GITHUB_SECRET

    elif account == 'vtuber':
        access_token = TWITTER_VTUBER_ACCESS_TOKEN
        secret = TWITTER_VTUBER_SECRET

    elif account == 'splatoon':
        access_token = TWITTER_SPLATTON_ACCESS_TOKEN
        secret = TWITTER_SPLATOON_SECRET

    else:
        print("NO MATCH")

    return TwitterApi(access_token, secret)
