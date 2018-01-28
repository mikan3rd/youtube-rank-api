import functools
from logging import getLogger
from typing import Any, Tuple, Union

from flask import jsonify as _jsonify
from flask import request


log = getLogger(__name__)


# APIメソッドの返り値用の静的型付けデータ
ApiResponseData = Union[dict, list, str, int, float]
ApiResponse = Union[Tuple[ApiResponseData, int], ApiResponseData]


def jsonify(func):
    '''レスポンスをjsonifyして返却する

    jsonifyへ渡すレスポンスの形式は、以下の形式(tuple or データ単体)

    data (,status_code)
        data: json化されるデータ
        status_code: レスポンスに設定されるステータスコード (デフォルト: 200)

    本デコレータは、Flask-Restfulを用いて実装したAPIでは修飾不要
    '''
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        results = func(*args, **kwargs)

        status_code = 200
        if isinstance(results, tuple):
            data = results[0]
            if len(results) > 1:
                status_code = results[1]
        else:
            data = results

        response = _jsonify(data)
        response.status_code = status_code

        return response

    return wrapper


def parse_params(types=[]):
    '''リクエストパラメータをパースし、修飾されているメソッドに引数として追加

    パース対象のパラメータはデコレータのtypes引数で指定が可能。
    types引数に指定したもののみ、同一名称の引数としてメソッド呼び出しに追加される。
    対象は、json, form, args。

    form, argsパラメータについては、複数項目設定されるもの(キー名がxxx[]となるもの)
    については、[]が除去されたlistとして取得される。
    '''
    def _parse_params(func):
        @functools.wraps(func)
        def wrapper(*_args, **_kwargs):

            if 'json' in types:
                _kwargs['json'] = request.get_json(silent=True)

            if 'form' in types:
                _kwargs['form'] = __parse_params(request.form)

            if 'args' in types:
                _kwargs['args'] = __parse_params(request.args)

            return func(*_args, **_kwargs)

        return wrapper

    return _parse_params


def create_error_data(message: str = '', detail: Any = '') -> dict:
    '''エラーレスポンス用のデータを生成する

    Args:
        message: エラー内容の説明
        detail: エラー内容詳細

    Returns:
        dict
    '''
    return {
        'error': {
            'message': message,
            'detail': detail,
        }
    }


def __parse_params(multi_dict) -> dict:
    '''MultiDict形式のパラメータを辞書形式に変換する.

    通常のキー名は同一キー名としてマッピングされる。
    キー名が'[]'で終わるデータは、キー名から'[]'が削除され、
    複数存在するデータは配列に変換されマッピングされる。

    Args:
        multi_dict: MultiDict系式のデータ

    Returns:
        変換された辞書データ
    '''
    pargs = {}
    for key in multi_dict.keys():
        if key.endswith('[]'):
            pargs[key[:-2]] = multi_dict.getlist(key)
        else:
            pargs[key] = multi_dict.get(key)

    return pargs


def not_found(detail=''):
    return create_error_data(message='Not Found', detail=detail), 404


def forbidden(detail=''):
    return create_error_data(message='Forbidden', detail=detail), 403
