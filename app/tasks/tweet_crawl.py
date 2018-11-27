import json
from pprint import pprint

import redis
import requests
from bs4 import BeautifulSoup
from settings import REDIS_URL

from app.tasks import twitter, twitter_tool


def github_status():
    url = 'https://status.github.com/messages'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "lxml")

    div_tag = soup.find('div', class_="message")
    class_list = div_tag.get('class')

    if 'good' in class_list:
        path = 'ok'

    elif 'minor' in class_list:
        path = 'caution'

    elif 'major' in class_list:
        path = 'error'

    else:
        print('GitHubStatus: no match')
        return

    title = div_tag.find('span', class_='title')
    text = title.text
    print(text)

    redis_key = 'GitHubStatus'
    r = redis.from_url(REDIS_URL)
    rcache = r.get(redis_key)

    if rcache:
        print("cache HIT!! %s" % (redis_key))
        redis_value = json.loads(rcache.decode())

        if redis_value == text:
            print('GitHubStatus: No Change!')
            return

    api = twitter.get_twitter_api('github')

    image_path = 'resources/images/github_%s.jpg' % path

    media = open(image_path, 'rb')
    response = api.upload_media(media)
    media_id = response['media_id_string']    # type: ignore

    status = text + "\n#github\n" + url

    # twitter_tool.post_tweet(
    #     username=api.username,
    #     password=api.password,
    #     status=status,
    #     image_path_list=[image_path]
    # )

    response = api.post_tweet(status=status, media_ids=[media_id])

    r.set(redis_key, json.dumps(text), ex=None)
    print("SUCCESS:crawl:GitHubStatus")


def hypnosismic():
    account = 'hypnosismic'

    redis_key = 'crawl:%s' % (account)
    r = redis.from_url(REDIS_URL)
    rcache = r.get(redis_key)

    redis_value = None
    if rcache:
        print("cache HIT!! %s" % (redis_key))
        redis_value = json.loads(rcache.decode())

    url = 'https://hypnosismic.com/news/'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "lxml")

    section_tag = soup.find('section', class_='lists')
    a_tag = section_tag.find('a')

    text = a_tag.find('span', class_='lists__list__text').text
    if redis_value == text:
        print('No Change:', account)
        return

    date = a_tag.find('span', class_='lists__list__date').text
    link = a_tag.get('href')

    status = '【更新】%s\n\n%s\n\n詳細は公式サイトをチェック！\n%s' % (date, text, link)
    pprint(status)

    api = twitter.get_twitter_api(account)
    # twitter_tool.post_tweet(
    #     username=api.username,
    #     password=api.password,
    #     status=status,
    # )

    response = api.post_tweet(status=status)

    r.set(redis_key, json.dumps(text), ex=None)
    print("SUCCESS:crawl:", account)
