from copy import deepcopy
from datetime import datetime, timedelta
from pprint import pprint

import requests
from firebase_admin import firestore
from settings import TIKTOK_AID, TIKTOK_DEVICE_ID

from app.server.helpers import firestore as helper_firestore
from app.server.helpers import gspread


SHEET_ID = "1gT0vS912lxkWLggJLjWygGbqSw6rLteRkFzlqsPZI44"
BASE_URL = "https://api.tiktokv.com/aweme/v1"

twitter_url = "https://twitter.com"
instagram_url = "https://www.instagram.com"
youtube_url = "https://www.youtube.com/channel"

feed_headers = {'User-Agent': 'AwemeI18n/3.1.1 (iPhone; iOS 11.4.1; Scale/2.00)'}
feed_params = {
    'account_region': 'JP',
    'aid': TIKTOK_AID,
    'app_language': 'ja',
    'carrier_region': 'JP',
    'count': 30,
    'device_id': TIKTOK_DEVICE_ID,
    'feed_style': 0,
    'filter_warn': 0,
    'is_my_cn': 0,
    'language': 'ja',
    'max_cursor': 0,
    'min_cursor': 0,
    'os_api': 18,
    'pull_type': 1,
    'sys_region': 'JP',
    'type': 0,
    'tz_name': 'Asia/Tokyo',
    'tz_offset': 32400,
    'volume': '0.00',
}

user_params = {
    'aid': TIKTOK_AID,
    'language': 'ja',
    'app_name': 'trill',
    'carrier_region': 'JP',
    'device_id': TIKTOK_DEVICE_ID,
    'account_region': 'JP',
    'sys_region': 'JP',
    'app_language': 'ja',
    'tz_name': 'Asia/Tokyo',
    'iid': '6642644565000111873'
}


def add_user():
    params = deepcopy(feed_params)
    params['ts'] = datetime.now().strftime('%s')
    res = requests.get(BASE_URL + "/feed/", headers=feed_headers, params=params)
    feed_data = res.json()

    user_list = []
    video_list = []
    for aweme in feed_data['aweme_list']:
        video = create_video_data(aweme)

        if video:
            video_list.append(video)

        uid = aweme['author'].get('uid')

        if not uid:
            continue

        user = get_user_detail(uid)

        if not user or not user.get('uid'):
            continue

        result = create_user_data(user)

        if not result:
            continue

        user_list.append(result)

    if user_list:
        helper_firestore.batch_update(
            collection='users',
            data_list=user_list,
            unique_key='uid'
        )

    if video_list:
        helper_firestore.batch_update(
            collection='videos',
            data_list=video_list,
            unique_key='aweme_id'
        )

    print("SUCCESS: tiktok, add_user")


def update_users():
    filter_time = datetime.now() - timedelta(weeks=1)

    helper_firestore.initialize_firebase()
    ref = firestore.client().collection('users')

    query = ref \
        .where('update_at', '<', filter_time) \
        .order_by('update_at') \
        .order_by('follower_count', direction=firestore.Query.DESCENDING) \
        .limit(100)

    docs = query.get()
    user_list = [doc.to_dict() for doc in docs]

    for user in user_list:
        uid = user.get('uid')

        if not uid:
            continue

        data = get_user_detail(uid)

        if not data or not data.get('uid'):
            continue

        result = create_user_data(data)

        if not result:
            continue

        user.update(result)

    if user_list:
        helper_firestore.batch_update(
            collection='users',
            data_list=user_list,
            unique_key='uid'
        )

    print("SUCCESS: tiktok, update_users")


def add_hashtag():
    params = deepcopy(user_params)
    params['count'] = 200
    res = requests.get(BASE_URL + "/recommend/challenge/", headers=feed_headers, params=params)
    data = res.json()
    challenge_list = data.get('challenge_list')
    challenge_list = sorted(challenge_list, key=lambda k: k.get('user_count', 0), reverse=True)
    print(len(challenge_list))

    results = []
    for challenge in challenge_list:
        result = create_hashtag_data(challenge)

        if not result:
            continue

        results.append(result)

    if results:
        helper_firestore.batch_update(
            collection='hashtags',
            data_list=results,
            unique_key='cid'
        )

    print("SUCCESS: tiktok, add_hashtag")


def trace_hashtag():
    helper_firestore.initialize_firebase()
    ref = firestore.client().collection('hashtags')

    filter_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(hours=9)
    query = ref \
        .where('update_at', '<', filter_time) \
        .order_by('update_at') \
        .order_by('user_count', direction=firestore.Query.DESCENDING) \
        .limit(100)

    docs = query.get()
    hashtag_list = [doc.to_dict() for doc in docs]

    results = []
    for hashtag in hashtag_list:
        params = deepcopy(user_params)
        params['ch_id'] = hashtag['cid']
        res = requests.get(BASE_URL + "/challenge/detail/", headers=feed_headers, params=params)
        data = res.json()
        challenge = data.get('ch_info')
        result = create_hashtag_data(challenge)

        if not result:
            continue

        hashtag.update(result)
        results.append(hashtag)

    if results:
        helper_firestore.batch_update(
            collection='hashtags',
            data_list=results,
            unique_key='cid'
        )

    print("SUCCESS: tiktok, trace_hashtag")


def get_user_detail(uid):
    params = deepcopy(user_params)
    params['user_id'] = uid
    res = requests.get(BASE_URL + "/user/", headers=feed_headers, params=params)

    data = res.json()
    return data.get('user')


def get_user_video(uid):
    params = deepcopy(user_params)
    params['user_id'] = uid
    res = requests.get(BASE_URL + "/aweme/post/", headers=feed_headers, params=params)

    data = res.json()

    pprint(data['aweme_list'][0])

    return data.get('user')


def create_user_data(data):
    result = {}

    for key, value in data.items():
        if value == "":
            continue

        if key == 'follower_count' and value <= 1000:
            return None

        if isinstance(value, str) or isinstance(value, bool) or isinstance(value, int):
            result[key] = value

        elif key == 'avatar_medium' or key == 'avatar_thumb':
            result[key] = value['url_list'][0].replace('.webp', '.jpeg')

        elif key == 'share_info':
            result['share_url'] = value.get('share_url').replace('/?', '')

    result = {
        k: v
        for k, v in result.items()
        if k in allowed_keys
    }

    return result


def create_hashtag_data(data):

    if not data.get('cid'):
        return None

    # invalid_characters = "~*/[]"

    result = {'stats': {}}
    for key, value in data.items():

        if key == 'user_count' and value <= 1000:
            return None

        if value == "":
            continue

        if isinstance(value, str) or isinstance(value, bool) or isinstance(value, int):
            result[key] = value

    date_key = datetime.now().strftime("%Y_%m_%d")
    result['stats'][date_key] = {
        'user_count': result.get('user_count'),
        'view_count': result.get('view_count'),
        'timestamp': firestore.SERVER_TIMESTAMP,
    }

    return result


def create_video_data(data):
    result = {}

    for key, value in data.items():

        if key == 'statistics':
            digg_count = value.get('digg_count', 0)

            if digg_count < 10000:
                return None

            result['digg_count'] = digg_count
            result['comment_count'] = value.get('comment_count', 0)

        elif key == 'author':
            result['uid'] = value.get('uid')
            result['nickname'] = value.get('nickname')

        elif key == 'video':
            result['download_url'] = value['download_addr']['url_list'][0]

        elif key == 'music':
            result['mid'] = value.get('mid')
            # result['music_album'] = value.get('album')
            # result['music_title'] = value.get('title')
            # result['music_author'] = value.get('author')

        elif key in ['aweme_id', 'share_url', 'desc', 'create_time']:
            result[key] = value

    return result


allowed_keys = [
    'avatar_medium',
    'avatar_thumb',
    'aweme_count',
    'custom_verify',
    'follower_count',
    'gender',
    'ins_id',
    'nickname',
    'share_url',
    'signature',
    'total_favorited',
    'twitter_id',
    'twitter_name',
    'youtube_channel_id',
    'youtube_channel_title',
    'short_id',
    'uid',
]


def update_spread_sheet():

    helper_firestore.initialize_firebase()
    ref = firestore.client().collection('hashtags')

    query = ref \
        .order_by('view_count', direction=firestore.Query.DESCENDING) \
        .limit(20)

    docs = query.get()

    label_list = []
    hashtag_list = []

    for doc in docs:
        hashtag = doc.to_dict()
        hashtag['ハッシュタグ'] = hashtag['cha_name']

        for _period, stat in hashtag['stats'].items():
            period = _period.replace('_', '/')

            if period not in label_list:
                label_list.append(period)

            hashtag[period] = stat['view_count']

        hashtag_list.append(hashtag)

    label_list = sorted(label_list)
    label_list.insert(0, 'ハッシュタグ')

    body = {
        'values': gspread.convert_to_sheet_values(label_list, hashtag_list),
        'majorDimension': 'COLUMNS',
    }
    gspread.update_sheet_values(SHEET_ID, '視聴回数合計', body, valueInputOption='RAW')

    del label_list[0]
    for hashtag in hashtag_list:

        prev_count = 0
        for period in label_list:

            count = hashtag.get(period)
            if not count:
                continue

            if prev_count == 0:
                hashtag[period] = ''

            else:
                hashtag[period] = count - prev_count

            prev_count = count

    del label_list[0]
    label_list.insert(0, 'ハッシュタグ')
    body = {
        'values': gspread.convert_to_sheet_values(label_list, hashtag_list),
        'majorDimension': 'COLUMNS',
    }

    gspread.update_sheet_values(SHEET_ID, '視聴回数（日別）', body, valueInputOption='RAW')

    print('SUCCESS: update_spread_sheet')
