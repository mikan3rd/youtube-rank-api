from logging import getLogger

from flask import Blueprint, request

from app.server.helpers.api import ApiResponse, jsonify


log = getLogger(__name__)

api_bp = Blueprint('daily_api', __name__)


@api_bp.route('/data/daily', methods=['GET'])
@jsonify
def get_keyword(*args, **kwargs) -> ApiResponse:
    '''
    まとめのキーワード一覧取得
    ---
    tags:
        - データ
    summary: まとめのキーワード一覧取得
    description: |
        まとめのキーワード一覧取得
        エリアが指定された場合は、そのエリアに存在するまとめのキーワードのみを返す

    operationId: get_keyword_list
    parameters:
        -
            $ref: "#/parameters/AreaAscii"
    responses:
        200:
            description: 取得成功
            schema:
                $ref: '#/definitions/response/Keywords'
    '''  # NOQA
    area = request.args.get('area')
    print("test:", area)
