from datetime import datetime, timedelta
from pprint import pprint
from time import sleep

import requests
from settings import TIKTOK_AID, TIKTOK_DEVICE_ID

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


def get_feed():
    response = gspread.get_sheet_values(SHEET_ID, 'users', "FORMULA")
    label_list, user_list = gspread.convert_to_dict_data(response)
    unique_ids = {str(user.get('uid')) for user in user_list}
    ts = datetime.now().strftime('%s')
    print("ts:", ts)

    url = "/feed/"
    print(url)

    feed_params['ts'] = ts

    res = requests.get(BASE_URL + url, headers=feed_headers, params=feed_params)
    data = res.json()

    new_num = 0
    try:
        aweme_list = data['aweme_list']
        print("len:", len(aweme_list))

        for aweme in aweme_list:
            user = aweme['author']
            result = create_user_data(user, unique_ids)

            if not result:
                continue

            user_list.append(result)
            new_num += 1

    except Exception as e:
        pprint(data)
        pprint(e)
        exit()

    print("NEW:", new_num)
    if new_num == 0:
        return

    user_list = sorted(user_list, key=lambda k: k.get('total_favorited', 0) or 0, reverse=True)
    body = {'values': gspread.convert_to_sheet_values(label_list, user_list)}
    gspread.update_sheet_values(SHEET_ID, 'users', body)
    print("SUCCESS!! get_feed")


def update_user_detail():
    response = gspread.get_sheet_values(SHEET_ID, 'users', "FORMULA")
    label_list, user_list = gspread.convert_to_dict_data(response)

    url = "/user/"
    print(url)

    today = datetime.now()
    new_num = 0
    for index, user in enumerate(user_list):
        try:
            uid = user.get('uid')

            if not uid:
                continue

            update_at = user.get('update_at')
            if update_at:
                # 前回の更新から24時間経っていない場合はスキップ
                time = datetime.strptime(update_at, '%Y/%m/%d %H:%M:%S') + timedelta(days=1)
                if time > today:
                    continue

            feed_params['user_id'] = uid
            res = requests.get(BASE_URL + url, headers=feed_headers, params=feed_params)
            data = res.json()

            if not data.get('user'):
                continue

            user_data = data['user']

            if not user_data.get('uid'):
                user['share_url'] = True
                continue

            result = create_user_data(user_data)

            if not result:
                continue

            user.update(result)
            new_num += 1
            print(index, user.get('nickname'))

            sleep(1)

            if new_num % 50 == 0:
                body = {'values': gspread.convert_to_sheet_values(label_list, user_list)}
                gspread.update_sheet_values(SHEET_ID, 'users', body)

        except Exception as e:
            pprint(e)
            break

    print("UPDATE:", new_num)
    if new_num == 0:
        return

    user_list = sorted(user_list, key=lambda k: k.get('total_favorited', 0) or 0, reverse=True)
    body = {'values': gspread.convert_to_sheet_values(label_list, user_list)}
    gspread.update_sheet_values(SHEET_ID, 'users', body)
    print("SUCCESS!! update_user_detail")


def create_user_data(user, unique_ids=set()):
    result = {}

    uid = str(user['uid'])
    if uid in unique_ids:
        return result

    language = user['language']
    if language != 'ja':
        return result

    update = False
    for key, value in user.items():
        if value == "":
            continue

        if isinstance(value, str) or isinstance(value, bool) or isinstance(value, int):
            result[key] = value

        elif key == 'avatar_medium' or key == 'avatar_larger':
            result[key] = value['url_list'][0]

        elif key == 'avatar_thumb':
            image = value['url_list'][0]
            result[key] = image
            result['thumb_image'] = '=IMAGE("%s")' % (image)

        elif key == 'share_info':
            result['share_url'] = value.get('share_url')

        update = True

    if update:
        now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        result['update_at'] = now

    return result


def create_markdown():
    response = gspread.get_sheet_values(SHEET_ID, 'users', "FORMULA")
    label_list, user_list = gspread.convert_to_dict_data(response)

    top = '''
:sparkling_heart: ハート
:family: ファン
:movie_camera: 動画

※ 現在、iPhoneだと画像が表示されないようです
    '''

    length = 50
    # agenda_list = []
    # rank_interval = [1, 11, 21]
    # for i, rank in enumerate(rank_interval):
    #     if i + 1 == len(rank_interval):
    #         last = length

    #     else:
    #         last = rank_interval[i + 1] - 1

    #     agenda = '-  <a href="#no%s"> No.%s 〜 No.%s</a>' % (rank, rank, last)
    #     agenda_list.append(agenda)

    # content_list = [top + '\n' + '\n'.join(agenda_list) + '\n']

    content_list = [top]
    for index, user in enumerate(user_list[:length]):

        sns_contents = []
        if user.get('share_url'):
            a = '<a href="%s">:link: TikTok</a>' % (user['share_url'])
            sns_contents.append(a)

        if user.get('twitter_name'):
            a = '<a href="%s/%s">:link: Twitter: @%s</a>' % (twitter_url, user['twitter_name'], user['twitter_name'])
            sns_contents.append(a)

        if user.get('ins_id'):
            a = '<a href="%s/%s">:link: Instagram: @%s</a>' % (instagram_url, user['ins_id'], user['ins_id'])
            sns_contents.append(a)

        if user.get('youtube_channel_id') and user.get('youtube_channel_title'):
            a = '<a href="%s/%s">:link: YouTube: %s</a>'  \
                % (youtube_url, user['youtube_channel_id'], user['youtube_channel_title'])
            sns_contents.append(a)

        content = '''
### No.{num}　{nickname}
<img src="{avatar_medium}" alt="{avatar_medium}" width="300px"></img>

```
{signature}
```

:sparkling_heart: {total_favorited}
:family: {follower_count}
:movie_camera: {aweme_count}

{sns}
        '''.format(num=index + 1, sns='\n'.join(sns_contents), **user)

        content_list.append(content)

    return '\n---\n'.join(content_list)
