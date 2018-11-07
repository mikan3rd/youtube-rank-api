import json
import urllib.request
from pprint import pprint

import redis
from settings import (
    REDIS_URL,
    TWITTER_AV_SOMMLIER_ACCESS_TOKEN,
    TWITTER_AV_SOMMLIER_SECRET,
    TWITTER_AV_ACTRESS_ACCESS_TOKEN,
    TWITTER_AV_ACTRESS_SECRET,
)

from app.server.helpers import dmm
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

    target = items[target_index]

    api = TwitterApi(TWITTER_AV_SOMMLIER_ACCESS_TOKEN, TWITTER_AV_SOMMLIER_SECRET)

    media = urllib.request.urlopen(target['imageURL']['large']).read()
    response = api.upload_media(media)
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
        if len(status) > 270:
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
