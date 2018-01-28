from . import data

blueprints = [  # TODO: 実装したAPIモジュールをここに記載する
    data.daily,
]


def get_blueprints() -> list:
    return blueprints
