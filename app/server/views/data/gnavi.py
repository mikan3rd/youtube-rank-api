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
    print("args:", args)
    endpoint = "http://webservice.recruit.co.jp/hotpepper/gourmet/v1/"

    params = {
        'key':  HOTPEPPER_API_KEY,
        'format': 'json',
        'lat': args['latitude'],
        'lng': args['longitude'],
        'lunch': args['lunch'],
        'range': args['range'],
    }

    response = requests.get(endpoint, params=params)
    result = response.json()
    # pprint(result)

    return result
