import json

from requests_oauthlib import OAuth1Session
from settings import TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET


class TwitterApi:

    def __init__(
        self,
        access_token,
        secret,
        query='',
        rakuten_query='',
        exclude_genre_id_list=[],
        target_list=[],
    ):

        self.api = OAuth1Session(
            TWITTER_CONSUMER_KEY,
            TWITTER_CONSUMER_SECRET,
            access_token,
            secret,
        )

        self.__query = query
        self.__rakuten_query = rakuten_query
        self.__exclude_genre_id_list = exclude_genre_id_list
        self.__target_list = target_list

    @property
    def query(self):
        return self.__query

    @property
    def rakuten_query(self):
        return self.__rakuten_query

    @property
    def exclude_genre_id_list(self):
        return self.__exclude_genre_id_list

    @property
    def target_list(self):
        return self.__target_list

    def get_account(self):
        endpoint = "https://api.twitter.com/1.1/account/verify_credentials.json"
        response = self.api.get(endpoint)
        return json.loads(response.text)

    def get_home_timeline(
        self,
        count=200,
        trim_user=False,
        exclude_replies=True,
        include_entities=False,
    ):
        endpoint = "https://api.twitter.com/1.1/statuses/home_timeline.json"
        params = {
            'count': count,
            'trim_user': trim_user,
            'exclude_replies': exclude_replies,
            'include_entities': include_entities,
        }
        response = self.api.get(endpoint, params=params)
        return json.loads(response.text)

    def get_user_timeline(self, screen_name, count=200):
        endpoint = "https://api.twitter.com/1.1/statuses/user_timeline.json"
        params = {
            'screen_name': screen_name,
            'count': count,
        }
        response = self.api.get(endpoint, params=params)
        return json.loads(response.text)

    def get_retweet_user(
        self,
        tweet_id,
        count=100,
        trim_user=False,
    ):
        endpoint = "https://api.twitter.com/1.1/statuses/retweets/%s.json" % (tweet_id)
        params = {
            'count': count,
            'trim_user': trim_user,
        }
        response = self.api.get(endpoint, params=params)
        return json.loads(response.text)

    def get_followers(
        self,
        user_id=None,
        screen_name=None,
        cursor=-1,
        count=200,
        skip_status=False,
        include_user_entities=True,
    ):
        endpoint = "https://api.twitter.com/1.1/followers/list.json"
        params = {
            'user_id': user_id,
            'screen_name': screen_name,
            'cursor': cursor,
            'count': count,
            'skip_status': skip_status,
            'include_user_entities': include_user_entities,
        }
        response = self.api.get(endpoint, params=params)
        return json.loads(response.text)

    def get_followings(
        self,
        user_id=None,
        screen_name=None,
        cursor=-1,
        count=200,
        skip_status=False,
        include_user_entities=True,
    ):
        endpoint = "https://api.twitter.com/1.1/friends/list.json"
        params = {
            'user_id': user_id,
            'screen_name': screen_name,
            'cursor': cursor,
            'count': count,
            'skip_status': skip_status,
            'include_user_entities': include_user_entities,
        }
        response = self.api.get(endpoint, params=params)
        return json.loads(response.text)

    def get_friendships(
        self,
        user_id=None,
        screen_name=None,
    ):
        endpoint = "https://api.twitter.com/1.1/friendships/lookup.json"
        params = {
            'user_id': user_id,
            'screen_name': screen_name,
        }
        response = self.api.get(endpoint, params=params)
        return json.loads(response.text)

    def get_search_tweet(
        self,
        q,
        count=100,
        lang='ja',
    ):
        endpoint = "https://api.twitter.com/1.1/search/tweets.json"
        params = {
            'q': q,
            'count': count,
            'lang': lang,
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
        attachment_url=None,
    ):
        endpoint = "https://api.twitter.com/1.1/statuses/update.json"
        params = {'status': status}

        if in_reply_to_status_id:
            params['in_reply_to_status_id'] = in_reply_to_status_id

        if media_ids:
            params['media_ids'] = ','.join(media_ids)

        if attachment_url:
            params['attachment_url'] = attachment_url

        print(status)

        response = self.api.post(endpoint, params=params)
        return json.loads(response.text)

    def post_follow(
        self,
        screen_name=None,
        user_id=None,
        follow=False,
    ):
        endpoint = "https://api.twitter.com/1.1/friendships/create.json"
        params = {
            'screen_name': screen_name,
            'user_id': user_id,
            'follow': follow,
        }
        response = self.api.post(endpoint, params=params)
        return json.loads(response.text)

    def post_unfollow(
        self,
        screen_name=None,
        user_id=None,
    ):
        endpoint = "https://api.twitter.com/1.1/friendships/destroy.json"
        params = {
            'screen_name': screen_name,
            'user_id': user_id,
        }
        response = self.api.post(endpoint, params=params)
        return json.loads(response.text)

    def post_retweet(
        self,
        tweet_id,
    ):
        endpoint = "https://api.twitter.com/1.1/statuses/retweet/%s.json" % (tweet_id)
        response = self.api.post(endpoint)
        return json.loads(response.text)
