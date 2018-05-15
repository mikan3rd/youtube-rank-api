from logging import getLogger

from flask import Blueprint, request

from app.server.helpers.api import ApiResponse, jsonify

from app.server.helpers.youtube_data import get_search_result

log = getLogger(__name__)


api_bp = Blueprint('daily_api', __name__)


@api_bp.route('/search', methods=['GET'])
@jsonify
def search(*args, **kwargs) -> ApiResponse:
    '''
    ランキング検索
    '''  # NOQA
    params = request.args
    print(params)
    return get_search_result(params)
