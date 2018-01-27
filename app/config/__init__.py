import os
import pickle
import re

import yaml


class ConfigLoader():
    __config = None

    @classmethod
    def initialize(cls, env: str='develop') -> None:
        config_dir = os.path.dirname(__file__)

        base_conf_path = '%s/config.yaml' % config_dir
        config = cls._load_config(base_conf_path)
        config.update(
            cls._load_configs(
                config_dir=config_dir,
                exclude_regexs=['^_', '^config.yaml$', '^env$'],
            )
        )

        env_conf = '%s/env/%s.yaml' % (config_dir, env)
        config.update(cls._load_config(env_conf))

        cls.__config = config

    @classmethod
    def _load_configs(cls, config_dir: str, exclude_regexs: list=[]) -> dict:
        '''指定されたディレクトリ以下のコンフィグを全て読み込む

        Args:
            config_dir: コンフィグ読み込み対象のディレクトリ
            exclude_regexs: 読み込み除外リスト(正規表現)

        Return:
            読み込まれたコンフィグ
        '''
        _config = {}
        for path in os.listdir(config_dir):
            for exclude_regex in exclude_regexs:
                pattern = re.compile(exclude_regex)
                if pattern.search(path):
                    break

            else:
                conf_path = '%s/%s' % (config_dir, path)
                if os.path.isdir(conf_path):
                    _config[path] = cls._load_configs(
                        conf_path, exclude_regexs=['^_']
                    )

                elif os.path.isfile(conf_path) and path.endswith('.yaml'):
                    conf_name = re.sub('\.yaml$', '', path)
                    _config[conf_name] = cls._load_config(conf_path)

        return _config

    @classmethod
    def _load_config(cls, conf_path: str) -> dict:
        '''指定されたパスのyamlファイルを読み込みdict形式で取得する.'''
        if not os.path.exists(conf_path):
            raise Exception('file not found %s' % conf_path)

        with open(conf_path, 'r', encoding='utf-8') as f:
            conf = yaml.load(f)
            if conf is not None:
                return conf
            else:
                return {}

    @classmethod
    def get_config(cls):
        if cls.__config is None:
            raise Exception('initialize実行前にget_configが実行されました')

        return _deepcopy(cls.__config)


def _deepcopy(obj: dict) -> dict:
    '''オブジェクトのdeepcopyを取得する.

    pythonのdeepcopyよりpickleでシリアライズ→デシリアライズした方が早い。
    コンフィグ程度の簡単な方の場合はこれで良い。
    '''
    return pickle.loads(pickle.dumps(obj))


def init_config(env: str='develop') -> None:
    '''アプリケーション設定を初期化する.

    Args:
        env:  環境情報 (production/staging/develop/slm)

    env, modeを元にそれぞれの設定(+デフォルト設定)を読み込み、
    アプリケーションの設定を初期化します。

    初期化操作はアプリケーションの起動時に１度だけ実行し、
    以降は、current_config()で呼び出すようにする。
    '''
    ConfigLoader.initialize(env)


def current_config() -> dict:
    '''アプリケーション設定を取得する.

    事前にアプリケーション設定の初期化をinit_config()で実施すること。
    以降は、本メソッドを用いて設定を取得可能。
    '''
    return ConfigLoader.get_config()


def get_db_url(usage_type: str) -> str:
    '''DBアクセス用URLを取得する

    Args:
        usage_type: コネクション情報のタイプ

    Return:
        DBアクセス用URL
    '''
    _config = current_config()
    dburl_base = _config.get('dburl')
    ci = _config.get('connection_info')[usage_type][0]
    return '%s%s:%s@%s/%s' % \
        (dburl_base, ci['user'], ci['password'], ci['host'], ci['database'])


def create_db_url(dburl_base, ci):
    return_str = '%s%s:%s@%s/%s' % (
        dburl_base, ci['user'], ci['password'], ci['host'], ci['database'])
    return return_str
