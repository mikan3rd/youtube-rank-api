from logging import getLogger

import requests
from flask import Blueprint
from settings import GNAVI_API_KEY, HOTPEPPER_API_KEY

from app.server.helpers.api import ApiResponse, jsonify, parse_params


log = getLogger(__name__)


api_bp = Blueprint('gnavi_api', __name__)


@api_bp.route('/gnavi', methods=['GET'])
@jsonify
@parse_params(types=['args'])
def gnavi(args) -> ApiResponse:
    '''
    ぐるなび
    '''  # NOQA
    print("args:", args)
    endpoint = "https://api.gnavi.co.jp/RestSearchAPI/20150630/"

    params = {
        'keyid':  GNAVI_API_KEY,
        'format': 'json',
        'latitude': args['latitude'],
        'longitude': args['longitude'],
    }

    response = requests.get(endpoint, params=params)
    result = response.json()

    return result


@api_bp.route('/hotpepper', methods=['GET'])
@jsonify
@parse_params(types=['args'])
def hotpeper(args) -> ApiResponse:
    endpoint = "http://webservice.recruit.co.jp/hotpepper/gourmet/v1/"

    params = {
        'key':  HOTPEPPER_API_KEY,
        'format': 'json',
        'lat': args['latitude'],
        'lng': args['longitude'],
        'lunch': args['lunch'],
        'wifi': args['wifi'],
        'range': args['range'],
        'count': 100,
    }

    response = requests.get(endpoint, params=params)
    data = response.json()
    shop_list = data['results']['shop']

    # food_list_tuple = {
    #     (shop['food']['code'], shop['food']['name'])
    #     for shop in shop_list
    #     if shop['food']['name']
    # }

    # food_list = [
    #     {'code': code, 'name': name}
    #     for code, name in food_list_tuple
    # ]
    # pprint(result)

    results = {
        'shop_list': shop_list[:10],
    }

    return results
