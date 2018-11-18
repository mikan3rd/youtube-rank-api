import json

import redis
import requests
from bs4 import BeautifulSoup
from settings import REDIS_URL

from app.tasks import twitter


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

    media = open('resources/images/github_%s.jpg' % path, 'rb')
    response = api.upload_media(media)
    media_id = response['media_id_string']    # type: ignore

    status = text + "\n#github\n" + url
    response = api.post_tweet(status=status, media_ids=[media_id])

    r.set(redis_key, json.dumps(text), ex=None)
    print("GitHubStatus: SUCCESS!!")
