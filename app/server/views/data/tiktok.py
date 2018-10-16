import json
import math
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
PER_PAGE = 20
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
    response = get_users_by_chache(
        params=args,
        sheet_name='users',
    )

    return response


def get_users_by_chache(params, sheet_name, expire=EXPIRE):
    print(params)
    key = str(params)

    r = redis.from_url(REDIS_URL)
    rcache = r.get(key)
    # rcache = False

    if rcache:
        print("cache HIT!! %s" % (key))
        result = json.loads(rcache.decode())
        return result

    response = gspread.get_sheet_values(SHEET_ID, sheet_name)
    person_label_list, person_list = gspread.convert_to_dict_data(response)

    if params.get('sort'):
        person_list = sorted(person_list, key=lambda k: int(k.get(params['sort'], 0) or 0), reverse=True)

    if params.get('gender'):
        person_list = [user for user in person_list if user.get('gender') in params['gender']]

    for index, person in enumerate(person_list):
        person['index'] = index

    start_num = 1
    page = int(params['page']) if params.get('page') else None
    if page:
        start_num = PER_PAGE * (page - 1)

    end_num = start_num + PER_PAGE

    result = []
    for user in person_list[start_num:end_num]:
        # 許可されたkeyのみ返す
        data = {
            k: v
            for k, v in user.items()
            if k in allowed_keys
        }

        data['avatar_thumb'] = data['avatar_thumb'].replace('.webp', '.jpeg')
        result.append(data)

    response = {
        'paging': create_paging_data(len(person_list), page),
        'user_list': result,
    }

    r.set(key, json.dumps(response), ex=expire)

    return response


def create_paging_data(total_count, page=None, per_page=PER_PAGE):
    '''ページングデータの作成
    Args:
        total_count(int): 全件数
        page(int): 表示対象のページ
        per_page(int): ページあたりの表示件数

    Returns:
        metadata(dict):
    '''
    if not page or not per_page:
        return {'total_count': total_count}

    max_page = \
        int(total_count / per_page) + \
        (1 if math.ceil(total_count % per_page) else 0)
    return {
        'total_count': total_count,
        'page': page,
        'max_page': max_page,
        'per_page': per_page,
    }
