from logging import getLogger

from flask import Blueprint

from app.server.helpers.api import ApiResponse, jsonify, parse_params


log = getLogger(__name__)


api_bp = Blueprint('healthcheck', __name__)


@api_bp.route('/', methods=['GET'])
@jsonify
def gnavi(args) -> ApiResponse:
    return 'Hello World'
