import requests
from settings import DUGA_APP_ID

endpoint = "http://affapi.duga.jp/search"


def search(offset=None):

    params = {
        'version': '1.1',
        'appid': DUGA_APP_ID,
        'agentid': 34754,
        'bannerid': '01',
        'format': 'json',
        'hits': 100,
    }

    res = requests.get(
        endpoint,
        params=params,
    )
    data = res.json()

    return data
