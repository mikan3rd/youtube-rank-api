import json
from pprint import pprint

import redis
import requests
from bs4 import BeautifulSoup
from settings import REDIS_URL

from app.tasks import twitter, twitter_tool


def github_status():
    url = 'https://www.githubstatus.com/'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "lxml")

    div_tag = soup.find('div', class_="incident-container")
    title_tag = div_tag.find('div', class_='incident-title')

    update_tag = div_tag.find('div', class_="update")
    strong_tag = update_tag.find('strong')
    description = strong_tag.next_sibling.replace(' -', '').strip()

    redis_key = 'GitHubStatus'
    r = redis.from_url(REDIS_URL)
    rcache = r.get(redis_key)

    if rcache:
        print("cache HIT!! %s" % (redis_key))
        redis_value = json.loads(rcache.decode())

        if redis_value == description:
            print('GitHubStatus: No Change!')
            return

    status = '【%s】\n%s\n\n%s\n\n%s' % (strong_tag.text, title_tag.text.strip(), description, url)

    class_list = title_tag.get('class')
    detail_class_list = update_tag.get('class')

    if 'impact-maintenance' in class_list:
        path = 'ok'

    elif 'impact-minor' in class_list:
        if 'resolved' in detail_class_list:
            path = 'ok'
        else:
            path = 'caution'

    elif 'impact-major' in class_list:
        if 'resolved' in detail_class_list:
            path = 'ok'
        else:
            path = 'error'

    else:
        print('GitHubStatus: no match')
        return

    print(path)

    api = twitter.get_twitter_api('github')

    image_path = 'resources/images/github_%s.jpg' % path

    media = open(image_path, 'rb')
    response = api.upload_media(media)
    media_id = response['media_id_string']    # type: ignore

    # twitter_tool.post_tweet(
    #     username=api.username,
    #     password=api.password,
    #     status=status,
    #     image_path_list=[image_path]
    # )

    response = api.post_tweet(status=status, media_ids=[media_id])

    r.set(redis_key, json.dumps(description), ex=None)
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

    status = '【更新】%s\n\n%s\n\n詳細は公式サイトをチェック！\n#ヒプノシスマイク\n%s' % (date, text, link)
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


def smash_bros():
    account = 'smash_bros'

    redis_key = 'crawl:%s' % (account)
    r = redis.from_url(REDIS_URL)
    rcache = r.get(redis_key)

    redis_value = None
    if rcache:
        print("cache HIT!! %s" % (redis_key))
        redis_value = json.loads(rcache.decode())

    url = "https://gamerch.com/smashbros/entry/58307"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "lxml")

    target = None
    for div_tag in soup.find_all("div", class_="mu__table"):

        if div_tag.find('th').text == 'VIPボーダー':
            target = div_tag.find('td')

    pprint(target)

    if not target:
        return

    text = target.text
    if text == redis_value:
        return

    contents = [span.text for span in target.find_all('span')]
    status = '【更新】スマブラSP VIPマッチボーダー\n\n%s\n\n#VIPボーダー\n#スマブラSP' % ("\n".join(contents))

    api = twitter.get_twitter_api(account)
    response = api.post_tweet(status=status)

    r.set(redis_key, json.dumps(text), ex=None)
    print("SUCCESS:crawl:", account)
