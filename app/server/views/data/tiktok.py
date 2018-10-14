import json
from logging import getLogger

import redis
from flask import Blueprint
from settings import REDIS_URL

from app.server.helpers import gspread
from app.server.helpers.api import ApiResponse, jsonify, parse_params


log = getLogger(__name__)
api_bp = Blueprint('tiktok_api', __name__)

SHEET_ID = "1cA3pIOPfRKw3v8oeArTsVOAszUWUO9cOZ4UKKAZ1RH4"
EXPIRE = 60 * 60 * 24
allowed_keys = [
    'index',
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
    'twitter_name',
    'youtube_channel_id',
    'youtube_channel_title',
    'short_id',
]


@api_bp.route('/tiktok/users', methods=['GET'])
@jsonify
@parse_params(types=['args'])
def get_users(args) -> ApiResponse:
    print("args:", args)
    user_list = get_users_by_chache(str(args), 'users')

    result = {
        'paging': None,
        'user_list': user_list,
    }

    return result


def get_users_by_chache(key, sheet_name, expire=EXPIRE):
    print(key)
    r = redis.from_url(REDIS_URL)
    rcache = r.get(key)
    # rcache = False

    if rcache:
        print("cache HIT!! %s" % (key))
        result = json.loads(rcache.decode())

    else:
        response = gspread.get_sheet_values(SHEET_ID, sheet_name)
        person_label_list, person_list = gspread.convert_to_dict_data(response)
        result = []
        for user in person_list[:50]:
            # 許可されたkeyのみ返す
            data = {
                k: v
                for k, v in user.items()
                if k in allowed_keys
            }

            data['avatar_thumb'] = data['avatar_thumb'].replace('.webp', '.jpeg')
            result.append(data)

        r.set(key, json.dumps(result), ex=expire)

    return result
