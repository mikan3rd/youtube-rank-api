from logging import getLogger

from flask import Blueprint
from settings import GNAVI_API_KEY, HOTPEPPER_API_KEY
import requests

from app.server.helpers.api import ApiResponse, jsonify, parse_params
from pprint import pprint

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
    pprint(result)

    return result


@api_bp.route('/hotpepper', methods=['GET'])
@jsonify
@parse_params(types=['args'])
def hotpeper(args) -> ApiResponse:
    '''
    ぐるなび
    '''  # NOQA
    endpoint = "http://webservice.recruit.co.jp/hotpepper/gourmet/v1/"

    params = {
        'key':  HOTPEPPER_API_KEY,
        'format': 'json',
        'lat': args['latitude'],
        'lng': args['longitude'],
        'lunch': args['lunch'],
        'wifi': args['wifi'],
        'range': args['range'],
        'food': args.get('food'),
        'count': 100,
    }

    response = requests.get(endpoint, params=params)
    data = response.json()
    shop_list = data['results']['shop']

    if args.get('food'):
        return {'shop_list': shop_list[:10]}

    food_list_tuple = {
        (shop['food']['code'], shop['food']['name'])
        for shop in shop_list
        if shop['food']['name']
    }

    food_list = [
        {'code': code, 'name': name}
        for code, name in food_list_tuple
    ]
    # pprint(result)

    results = {
        'shop_list': shop_list[:10],
        'food_list': sorted(food_list, key=lambda x: x['code']),
    }

    return results


@api_bp.route('/hotpepper/food_category', methods=['GET'])
@jsonify
def get_hotpeper_food_category() -> ApiResponse:
    '''
    ぐるなび
    '''  # NOQA
    endpoint = "http://webservice.recruit.co.jp/hotpepper/food_category/v1/"

    params = {
        'key':  HOTPEPPER_API_KEY,
        'format': 'json',
    }

    response = requests.get(endpoint, params=params)
    result = response.json()
    # pprint(result)

    return result


@api_bp.route('/hotpepper/food', methods=['GET'])
@jsonify
@parse_params(types=['args'])
def get_hotpeper_food(args) -> ApiResponse:
    '''
    ぐるなび
    '''  # NOQA
    endpoint = "http://webservice.recruit.co.jp/hotpepper/food/v1/"

    params = {
        'key':  HOTPEPPER_API_KEY,
        'format': 'json',
        'food_category': args.get('food_category'),
    }

    response = requests.get(endpoint, params=params)
    result = response.json()
    # pprint(result)

    return result
