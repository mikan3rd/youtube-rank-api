import functools
import os
import re
from contextlib import contextmanager
from logging import getLogger
from typing import Callable, Dict, List, Optional, Set, Union

from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import DetachedInstanceError

from app.config import current_config

log = getLogger(__name__)


def _get_modules() -> List[str]:
    modules = []
    _dir = os.path.dirname(__file__)
    for _file in os.listdir(_dir):
        if _file.startswith('__'):
            continue
        if not _file.endswith('.py'):
            continue

        modules.append(re.sub(r'\.py$', '', _file))

    return modules


# import * 用にモデルのモジュール一覧を生成
__all__ = _get_modules()


# ベースモデル
BaseModel = declarative_base()


class ModelMixin():

    def to_dict(
        self,
        columns: Optional[set]=None,
        exclude_columns: Optional[set]=None,
        with_private_columns: Union[bool, list]=False,
    ) -> dict:
        '''モデルインスタンスをdict化する

        リレーション先のモデルインスタンスがセッションからデタッチされている場合、
        対象のカラムはデータに含まれない。
        これは、相互リレーションが組まれているモデルを再帰的にdict化しようとした場合に、
        リレーション先のさらにリレーション先を取得する必要が出てきてしまい、連鎖してしまうため。

        Args:
            columns: 取得対象のカラム名 (未指定の場合全て取得)
            exclude_columns: 取得対象外のカラム名
            with_private_columns: プライベート情報を含めるか
                True: すべてのプライベート情報を含める
                List[class]: 指定クラスのプラーベート情報を含める
        '''

        mapper = inspect(self)
        data = {}  # type: dict
        for column in mapper.attrs:
            key = column.key

            if not columns or key in columns:

                # 継承している各クラスからprivate_columnを集約する
                private_columns = set()  # type: set
                if with_private_columns is False:
                    private_columns = collect_private_columns(self.__class__)
                elif isinstance(with_private_columns, list):
                    private_columns = collect_private_columns(
                        self.__class__, *with_private_columns
                    )
                if key in private_columns:
                    continue

                if exclude_columns and key in exclude_columns:
                    continue

                try:
                    value = column.value
                except DetachedInstanceError:
                    continue

                if hasattr(value, 'to_dict'):
                    data[key] = value.to_dict()
                elif isinstance(value, list):
                    data[key] = [
                        v.to_dict() if hasattr(v, 'to_dict') else v
                        for v in value
                    ]
                elif isinstance(value, set):
                    data[key] = {
                        v.to_dict() if hasattr(v, 'to_dict') else v
                        for v in value
                    }
                elif isinstance(value, tuple):
                    data[key] = tuple([
                        v.to_dict() if hasattr(v, 'to_dict') else v
                        for v in value
                    ])
                elif isinstance(value, dict):
                    data[key] = {
                        k: v.to_dict() if hasattr(v, 'to_dict') else v
                        for k, v in value.items()
                    }
                else:
                    data[key] = column.value

        return data


@functools.lru_cache(maxsize=256)
def collect_private_columns(_class, *except_classes) -> Set[str]:
    private_columns = set()  # type: set
    for superclass in _class.mro():
        if superclass not in except_classes:
            if hasattr(superclass, 'private_columns'):
                private_columns |= superclass.private_columns

    return private_columns


@contextmanager
def session_scope(usage_type: str='r'):
    '''セッションを取得

    Args:
        usage_type (str) : 接続先タイプ (configに記載)

    Return:
        (Session) : セッションオブジェクト
    '''
    Session = SessionManager.get_configured_session_class(usage_type)
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def with_session(usage_type: str, expunge: bool):
    '''SQL Alchemyのローカルセッションの自動挿入を行うデコレータを返す

    本デコレータの動作は以下。
      - メソッド引数のkwargsにsessionが含まれている場合:
            特に何もしない。
      - メソッド引数のkwargsにsessionが含まれていない場合:
            session_scope(usage_type=usage_type)でローカルセッションを生成し、
            kwargs['session']に追加し、funcに渡す。
            また、expunge=Trueが指定されている場合、ローカルセッションを抜ける前に、
            session.expunge_all()を実行し、モデルインスタンスのローカルセッションからの
            切り離しを行います。

    上記より、本デコレータで修飾されるメソッドは、kwawgsとしてsessionを持つ必要がある。

    ローカルセッションのexpungeについては以下について注意すること。
      - 更新/削除を行うメソッドをデコレートする場合:
            必ずexpunge=Falseとすること
            expunge=Trueだと、session.commit()前にexpungeが実行され、操作が取り
            消されるため注意すること。
      - データの取得を行いモデルインスタンスを返す場合:
            必ずexpunge=Trueとすること
            expunge=Falseだと、ローカルセッションを抜けるタイミングでexpiredとなり、
            ローカルセッション外でインスタンスのデータにアクセスするとエラーが発生する。
    '''
    def _with_session(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if 'session' in kwargs:
                return func(*args, **kwargs)
            else:
                with session_scope(usage_type=usage_type) as session:
                    kwargs['session'] = session
                    results = func(*args, **kwargs)
                    if expunge:
                        session.expunge_all()
                    return results

        return wrapper

    return _with_session


class SessionManager():
    _connection_infos = {}  # type: dict
    _configured_sessions = {}  # type: dict

    @classmethod
    def get_engine(cls, _type: str):
        config = current_config()
        dburl = config.get('dburl')
        failover = []

        # 接続情報を取得する
        # 以下の優先順で取得
        # 1. set_connection_infoでセットされた値
        # 2. configに記載の値
        connection_info = cls._connection_infos.get(
            _type, config.get('connection_info', {}).get(_type, []))
        for c in connection_info:
            failover.append({
                'user': c.get('user'),
                'password': c.get('password'),
                'host': c.get('host'),
                'database': c.get('database'),
            })

        return create_engine(
            dburl,
            connect_args={'failover': failover},
            echo=config.get('sql_debug'),
        )

    @classmethod
    def set_connection_info(cls, _type: str, connection_info: Dict) -> None:
        cls._connection_infos[_type] = connection_info
        if _type in cls._configured_sessions:
            del cls._configured_sessions[_type]

    @classmethod
    def get_configured_session_class(cls, _type: str):
        '''設定済みセッション情報を取得する

        Args:
            _type (str) : 接続先タイプ
        '''
        if _type in cls._configured_sessions:
            return cls._configured_sessions[_type]

        engine = cls.get_engine(_type)
        Session = sessionmaker(bind=engine)
        cls._configured_sessions[_type] = Session

        return cls._configured_sessions[_type]
