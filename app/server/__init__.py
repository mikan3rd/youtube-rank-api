import os
from os.path import dirname, join

from dotenv import load_dotenv
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
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    host = config.get('server').get('host')
    port = os.environ.get('PORT', 3333)
    print("host:", host)
    print("port:", port)

    flask_server.run(
        host=host,
        port=int(port),
        threaded=config.get('server').get('threaded'),
        debug=config.get('server_debug'),
    )
