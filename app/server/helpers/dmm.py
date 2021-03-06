
import requests
from settings import DMM_AFFILIATE_ID, DMM_API_ID


dmm_endpoint = "https://api.dmm.com/affiliate/v3"


def search_actress(keyword=None, actress_id=None):
    endpoint = '/ActressSearch'

    params = {
        'api_id': DMM_API_ID,
        'affiliate_id': DMM_AFFILIATE_ID,
        'actress_id': actress_id,
        'keyword': keyword,
        'output': 'json',
    }

    res = requests.get(
        dmm_endpoint + endpoint,
        params=params,
    )
    data = res.json()

    # pprint(data['result']['actress'])
    return data


def search_genre(floor_id=43, hits=500):
    endpoint = '/GenreSearch'

    params = {
        'api_id': DMM_API_ID,
        'affiliate_id': DMM_AFFILIATE_ID,
        'floor_id': floor_id,
        'hits': hits,
        'output': 'json',
    }

    res = requests.get(
        dmm_endpoint + endpoint,
        params=params,
    )
    data = res.json()

    from pprint import pprint
    pprint(data)

    return data


def search_items(
    site='FANZA',
    service='digital',
    floor='videoa',
    keyword=None,
    article=None,
    article_id=None,
    hits=100,
    offset=1,
):
    endpoint = '/ItemList'

    params = {
        'api_id': DMM_API_ID,
        'affiliate_id': DMM_AFFILIATE_ID,
        'site': site,
        'service': service,
        'floor': floor,
        'keyword': keyword,
        'article': article,
        'article_id': article_id,
        'hits': hits,
        'offset': offset,
        'output': 'json',
    }

    res = requests.get(
        dmm_endpoint + endpoint,
        params=params,
    )
    data = res.json()

    # from pprint import pprint
    # pprint(data)

    return data
