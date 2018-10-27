import json

import redis
import requests
from bs4 import BeautifulSoup
from requests_oauthlib import OAuth1Session
from settings import (
    REDIS_URL,
    TWITTER_CONSUMER_KEY,
    TWITTER_CONSUMER_SECRET,
    TWITTER_GITHUB_ACCESS_TOKEN,
    TWITTER_GITHUB_SECRET
)


class TwitterApi:

    def __init__(self, access_token, secret):
        self.api = OAuth1Session(
            TWITTER_CONSUMER_KEY,
            TWITTER_CONSUMER_SECRET,
            access_token,
            secret,
        )

    def get_user_timeline(self, screen_name, count=200):
        endpoint = "https://api.twitter.com/1.1/statuses/user_timeline.json"
        params = {
            'screen_name': screen_name,
            'count': count,
        }
        response = self.api.get(endpoint, params=params)
        return json.loads(response.text)

    def upload_media(self, media):
        endpoint = "https://upload.twitter.com/1.1/media/upload.json"
        files = {'media': media}
        response = self.api.post(endpoint, files=files)
        return json.loads(response.text)

    def post_tweet(
        self,
        status,
        media_ids=None,
        in_reply_to_status_id=None,
    ):
        endpoint = "https://api.twitter.com/1.1/statuses/update.json"
        params = {'status': status}

        if in_reply_to_status_id:
            params['in_reply_to_status_id'] = in_reply_to_status_id

        if media_ids:
            params['media_ids'] = media_ids

        response = self.api.post(endpoint, params=params)
        return json.loads(response.text)


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
    exit()

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
        exit()

api = TwitterApi(TWITTER_GITHUB_ACCESS_TOKEN, TWITTER_GITHUB_SECRET)

media = open('resources/images/github_%s.jpg' % path, 'rb')
response = api.upload_media(media)
# pprint(response)
media_id = response['media_id_string']    # type: ignore

response = api.post_tweet(status=text + "\n#github", media_ids=[media_id])
# pprint(response)

r.set(redis_key, json.dumps(text), ex=None)
print("GitHubStatus: SUCCESS!!")

# response = api.get_user_timeline('git_hub_status')
# pprint(response)
