import requests
from settings import RAKUTEN_AFFILIATE_ID, RAKUTEN_APP_ID


base_url = 'https://app.rakuten.co.jp/services/api'


def search_ichiba_item(
    keyword,
    formatVersion=2,
    imageFlag=1,
    carrier=2,
    orFlag=1,
    field=0,
    page=1,
    availability=1,
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
        'field': field,
        'page': page,
        'availability': availability,
    }

    res = requests.get(base_url + endpoint, params=params)
    data = res.json()

    return data


def ranking_ichiba_item(
    formatVersion=2,
    page=1.
):

    endpoint = '/IchibaItem/Ranking/20170628'

    params = {
        'applicationId': RAKUTEN_APP_ID,
        'affiliateId': RAKUTEN_AFFILIATE_ID,
        'formatVersion': formatVersion,
        'page': page,
    }

    res = requests.get(base_url + endpoint, params=params)
    data = res.json()

    return data


def get_travel_ranking(
    formatVersion=2,
    genre='all,onsen,premium'
):
    endpoint = '/Travel/HotelRanking/20170426'

    params = {
        'applicationId': RAKUTEN_APP_ID,
        'affiliateId': RAKUTEN_AFFILIATE_ID,
        'formatVersion': formatVersion,
        'genre': genre,
    }

    res = requests.get(base_url + endpoint, params=params)
    return res.json()


def get_travel_detail(
    hotelNo,
    formatVersion=2,
    hotelThumbnailSize=3,
    responseType='large',
):
    endpoint = '/Travel/HotelDetailSearch/20170426'
    params = {
        'applicationId': RAKUTEN_APP_ID,
        'affiliateId': RAKUTEN_AFFILIATE_ID,
        'formatVersion': formatVersion,
        'hotelNo': hotelNo,
        'hotelThumbnailSize': hotelThumbnailSize,
        'responseType': responseType,
    }

    res = requests.get(base_url + endpoint, params=params)
    return res.json()
