from flask import Flask

from app.config import current_config
from app.server.helpers.request import after_request
from app.server.views import get_blueprints


def init_server():
    '''サーバーの初期化'''
    flask_server = Flask(__name__)

    blueprints = get_blueprints()
    for blueprint in blueprints:
        flask_server.register_blueprint(blueprint.api_bp)

    @flask_server.after_request
    def _after_request(response):
        return after_request(response)

    return flask_server


def run(port=None) -> None:
    '''サーバーの実行

    Args:
        port: サーバーのLISTENポート
              未指定の場合、コンフィグ(server.port)記載の値が使用される
    '''
    flask_server = init_server()

    config = current_config()
    flask_server.run(
        host=config.get('server').get('host'),
        port=port if port else config.get('server').get('port'),
        threaded=config.get('server').get('threaded'),
        debug=config.get('server_debug'),
    )
