from datetime import datetime, timedelta
from pprint import pprint
from time import sleep

import requests
from firebase_admin import firestore
from settings import TIKTOK_AID, TIKTOK_DEVICE_ID

from app.server.helpers import firestore as helper_firestore
from app.server.helpers import gspread


SHEET_ID = "1cA3pIOPfRKw3v8oeArTsVOAszUWUO9cOZ4UKKAZ1RH4"
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
}


def add_user():
    feed_params['ts'] = datetime.now().strftime('%s')
    res = requests.get(BASE_URL + "/feed/", headers=feed_headers, params=feed_params)
    feed_data = res.json()

    user_list = []
    for aweme in feed_data['aweme_list']:
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

    print("SUCCESS: tiktok, add_user")


def update_users():
    filter_time = datetime.now() - timedelta(weeks=1)

    helper_firestore.initialize_firebase()
    ref = firestore.client().collection('users')

    query = ref \
        .where('update_at', '<', filter_time) \
        .limit(100)

    docs = query.get()
    user_list = [doc.to_dict() for doc in docs]

    for user in user_list:
        uid = user.get('uid')

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

    print("SUCCESS: tiktok, update_users")


def get_user_detail(uid):
    user_params['user_id'] = uid
    res = requests.get(BASE_URL + "/user/", headers=feed_headers, params=user_params)

    data = res.json()
    return data.get('user')


def create_user_data(user, unique_ids=set()):
    result = {}

    uid = str(user['uid'])
    if uid in unique_ids:
        return result

    language = user['language']
    if language != 'ja':
        return result

    # update = False
    for key, value in user.items():
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

    #     update = True

    # if update:
    #     now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    #     result['update_at'] = now

    result = {
        k: v
        for k, v in result.items()
        if k in allowed_keys
    }

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
