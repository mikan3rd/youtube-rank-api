from logging import getLogger

from flask import Blueprint

from app.server.helpers.api import jsonify


log = getLogger(__name__)


api_bp = Blueprint('healthcheck', __name__)


@api_bp.route('/', methods=['GET'])
@jsonify
def healthcheck():
    return 'Hello World'
