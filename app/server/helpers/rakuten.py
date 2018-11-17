import requests
from settings import RAKUTEN_APP_ID, RAKUTEN_AFFILIATE_ID


base_url = 'https://app.rakuten.co.jp/services/api'


def search_ichiba_item(
    keyword,
    formatVersion=2,
    imageFlag=1,
    carrier=2,
):
    endpoint = '/IchibaItem/Search/20170706'

    params = {
        'applicationId': RAKUTEN_APP_ID,
        'affiliateId': RAKUTEN_AFFILIATE_ID,
        'formatVersion': formatVersion,
        'imageFlag': imageFlag,
        'keyword': keyword,
        'carrier': carrier,
    }

    res = requests.get(base_url + endpoint, params=params)
    data = res.json()

    # from pprint import pprint
    # pprint(data['Items'][0])

    return data
