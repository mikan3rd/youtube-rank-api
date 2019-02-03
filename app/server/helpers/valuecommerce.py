from pprint import pprint

import requests


VALUECOMMERCE_TOKEN = '1e8ddddf040b6eedb7ba189977be6a35'
base_url = 'http://webservice.valuecommerce.ne.jp'


def search_category(
    category_level=None,
):
    endpoint = '/productdb/category'

    params = {
        'token': VALUECOMMERCE_TOKEN,
        'category_level': category_level,
        'format': 'json',
    }

    res = requests.get(
        base_url + endpoint,
        params=params,
    )
    print(res.status_code)

    data = res.json()

    for item in data['items']:
        print(item['title'])

    return data


def search_product(
    keyword='',
    category='',
    adult='y',
    results_per_page=50,
):
    endpoint = '/productdb/search'

    params = {
        'token': VALUECOMMERCE_TOKEN,
        'keyword': keyword,
        'category': category,
        'adult': adult,
        'results_per_page': results_per_page,
        'format': 'json',
    }

    res = requests.get(
        base_url + endpoint,
        params=params,
    )
    print(res.status_code)

    data = res.json()
    # for d in data['items']:
    #     pprint(d)

    return data
