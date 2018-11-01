import json

from requests_oauthlib import OAuth1Session
from settings import TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET


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
