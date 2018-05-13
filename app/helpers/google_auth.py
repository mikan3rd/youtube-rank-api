from logging import getLogger

import oauth2client.client
import settings
from apiclient.discovery import build


log = getLogger(__name__)


def get_youtube_credentials():
    credentials = get_credentials(
        settings.CLIENT_EMAIL,
        settings.PRIVATE_KEY,
    )
    youtube = get_youtube(credentials)
    return youtube


def get_credentials(client_email, private_key):
    print(private_key.encode())

    try:
        SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
        credentials = oauth2client.client \
            .SignedJwtAssertionCredentials(
                client_email,
                private_key.encode(),
                SCOPES,
            )
        return credentials

    except Exception as e:
        raise Exception('credentials取得に失敗しました %s' % e)


def get_youtube(credentials):
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"
    try:
        youtube = build(
            YOUTUBE_API_SERVICE_NAME,
            YOUTUBE_API_VERSION,
            credentials=credentials,
        )
        return youtube

    except Exception as e:
        raise Exception('youtube取得に失敗しました %s' % e)
