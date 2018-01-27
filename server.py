#!/usr/bin/env python

import argparse

from app.config import current_config, init_config
from app.logger import setup_logger


# 起動パラメータの取得
parser = argparse.ArgumentParser()
parser.add_argument(
    '-e', '--env', help='実行環境', type=str,
    choices=[
        'develop',
        'staging',
        'production',
        'slm',
        'slm-staging'
    ],
    default='develop',
)
parser.add_argument(
    '-m', '--mode', help='起動モード', type=str,
    choices=['external', 'internal'],
    default='external',
)
parser.add_argument('-p', '--port', help='ポート', type=int, default=None)
args = parser.parse_known_args()[0]

# コンフィグの初期化、取得
init_config(env=args.env)
config = current_config()

# loggerのセットアップ
logging_type = 'server'
setup_logger(
    config=config.get('logging').get(logging_type),
    log_dir=config.get('server').get('log_dir'),
    debug=config.get('server').get('debug')
)


if __name__ == '__main__':
    # サーバーの実行
    from app import server  # NOQA

    server.run(port=args.port, mode=args.mode)
