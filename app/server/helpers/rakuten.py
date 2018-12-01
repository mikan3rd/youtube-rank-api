import requests
from settings import RAKUTEN_AFFILIATE_ID, RAKUTEN_APP_ID


base_url = 'https://app.rakuten.co.jp/services/api'


def search_ichiba_item(
    keyword,
    formatVersion=2,
    imageFlag=1,
    carrier=2,
    orFlag=1,
):
    endpoint = '/IchibaItem/Search/20170706'

    params = {
        'applicationId': RAKUTEN_APP_ID,
        'affiliateId': RAKUTEN_AFFILIATE_ID,
        'formatVersion': formatVersion,
        'imageFlag': imageFlag,
        'keyword': keyword,
        'carrier': carrier,
        'orFlag': orFlag,
    }

    res = requests.get(base_url + endpoint, params=params)
    data = res.json()

    # from pprint import pprint
    # pprint(data['Items'][0])

    return data


def ranking_ichiba_item(
    formatVersion=2,
):

    endpoint = '/IchibaItem/Ranking/20170628'

    params = {
        'applicationId': RAKUTEN_APP_ID,
        'affiliateId': RAKUTEN_AFFILIATE_ID,
        'formatVersion': formatVersion,
    }

    res = requests.get(base_url + endpoint, params=params)
    data = res.json()

    # from pprint import pprint
    # pprint(data['Items'][0])

    return data
