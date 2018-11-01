import json
import urllib.request
from pprint import pprint

import redis
from settings import (
    REDIS_URL,
    TWITTER_AV_SOMMLIER_ACCESS_TOKEN,
    TWITTER_AV_SOMMLIER_SECRET
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
    maker = '【メーカー】' + item_info['maker'][0]['name'] if item_info.get('maker') else ''
    series = '【シリーズ】' + item_info['series'][0]['name'] if item_info.get('series') else ''
    actress_list = [
        actress['name']
        for actress in item_info.get('actress', [])
        if isinstance(actress['id'], int)
    ]
    actress = '【女優】' + '   '.join(actress_list) if actress_list else ''

    content_list = [
        target['title'],
        '',
        actress,
        # maker,
        # series,
        '【ジャンル】' + '   '.join([genre.get('name') for genre in item_info['genre']]),
        '',
        '【詳細URL】' + target['affiliateURL'],
    ]

    status = '\n'.join(content_list)
    print(status)
    response = api.post_tweet(status=status, media_ids=[media_id])

    if response.get('errors'):
        del content_list[2]
        status = '\n'.join(content_list)
        print(status)
        response = api.post_tweet(status=status, media_ids=[media_id])

    if response.get('errors'):
        del content_list[2]
        status = '\n'.join(content_list)
        print(status)
        response = api.post_tweet(status=status, media_ids=[media_id])

    title_list.append(target['content_id'])
    r.set(redis_key, json.dumps(list(set(title_list))), ex=None)
    print("SUCCESS: twitter:av_sommlier")
