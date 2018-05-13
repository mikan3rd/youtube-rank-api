from datetime import datetime, time, timedelta, timezone
from logging import getLogger
from pprint import pprint

import pytz
from apiclient.discovery import build
from settings import DEVELOPER_KEY


log = getLogger(__name__)

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

JST = timezone(timedelta(hours=+9), 'JST')
tz = pytz.timezone('Asia/Tokyo')


def get_search_result(query=None):
    search_time = datetime.now(tz).date()
    yesterday = search_time - timedelta(days=1)
    weeks = search_time - timedelta(weeks=1)
    month = search_time - timedelta(weeks=4)

    search_time = tz.localize(
        datetime.combine(weeks, time(0, 0)),
        is_dst=None
    )

    params = {
        'q': query or '',
        'part': "id,snippet",
        'type': "video",
        'order': 'viewCount',
        'maxResults': 20,
        'publishedAfter': search_time.isoformat(),
        'regionCode': 'JP',
        'relevanceLanguage': 'ja',
        'videoCategoryId': None,
        # 'location': '35.39,139.44',
        # 'locationRadius': '1000km',
    }

    pprint(params)

    youtube = build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        developerKey=DEVELOPER_KEY
    )

    search_response = youtube.search().list(**params).execute()

    video_list = []
    channel_list = []
    for res in search_response['items']:
        snippet = res['snippet']
        channel_id = snippet['channelId']
        if channel_id not in channel_list:
            channel_list.append(channel_id)
            video_list.append(res)

    id_list = [video['id']['videoId'] for video in video_list]

    video_response = youtube.videos().list(
        part="snippet,statistics,player",
        id=','.join(id_list)
    ).execute()

    results = []
    for index, res in enumerate(video_list):
        snippet = res['snippet']
        video = video_response['items'][index]
        video['rank'] = index + 1
        view_count = video['statistics']['viewCount']
        # print(
        #     index + 1, view_count, '回',
        #     snippet['channelTitle'], snippet['title'])

        results.append(video)

    return results
