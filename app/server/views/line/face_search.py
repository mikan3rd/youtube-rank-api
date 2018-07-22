import json
from io import BytesIO

import redis
import settings
from flask import Blueprint, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    CarouselColumn,
    CarouselTemplate,
    # ConfirmTemplate,
    ImageMessage,
    MessageEvent,
    PostbackAction,
    PostbackEvent,
    TemplateSendMessage,
    TextMessage,
    TextSendMessage,
    URIAction,
    ImageCarouselColumn
)

from app.server.helpers.face import get_face_detect, get_face_identify


api_bp = Blueprint('face_search_api', __name__)


line_bot_api = LineBotApi(settings.DRINKEE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.DRINKEE_CHANNEL_SECRET)

wiki_url = "https://ja.wikipedia.org/wiki"
no_image_url = "https://upload.wikimedia.org/wikipedia/ja/b/b5/Noimage_image.png"


@api_bp.route("/line/face_search", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    print("body:", body)

    # handle webhook body
    try:
        handler.handle(body, signature)

    except InvalidSignatureError as e:
        print("InvalidSignatureError:", e)
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # text = event.message.text

    messages = [
        TextSendMessage(text='画像を送ってみてね!'),
    ]

    reply_message(event, messages)


@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):

    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)
    image = BytesIO(message_content.content)

    try:
        detect_results = get_face_detect(image=image)

        if isinstance(detect_results, str):
            reply_message(event, TextSendMessage(text=detect_results))
            return

        identify_results = get_face_identify([detect_results[0]['faceId']])

        if isinstance(identify_results, str):
            reply_message(event, TextSendMessage(text=identify_results))
            return

        results = identify_results[0]
        candidates = results['candidates']

        if len(candidates) == 0:
            reply_message(event, TextSendMessage(text='似ている顔が見つかりませんでした'))
            return

        r = redis.from_url(settings.REDIS_URL)
        contents = []

        for candidate in candidates:
            person_id = candidate['personId']
            rcache = r.get(person_id)

            if not rcache:
                continue

            data = json.loads(rcache.decode())

            image = no_image_url
            images = data.get('images')

            for image_url in images:
                if image_url.startswith('https://'):
                    image = image_url
                    break

            content = {
                'name': data.get('name'),
                'image': image,
                'person_id': person_id,
                'confidence': candidate['confidence']
            }
            print(content)
            contents.append(content)

        columns = [
            CarouselColumn(
                thumbnail_image_url=content['image'],
                title=content['name'],
                text='類似度：%s' % (
                    str(round(content['confidence'] * 100, 2)) + '%'),
                actions=[
                    PostbackAction(
                        label='画像をもっと見る',
                        display_text='画像をもっと見る',
                        data=person_id,
                    ),
                    URIAction(
                        label='Wikipediaを開く',
                        uri='%s/%s' % (wiki_url, content['name']),
                    ),
                    URIAction(
                        label='画像出典元',
                        uri=content['image'],
                    )
                ]
            )
            for content in contents[:10]
        ]

        messages = TemplateSendMessage(
            alt_text='template',
            template=CarouselTemplate(columns=columns),
        )

        reply_message(event, messages)

    except Exception as e:
        print("error:", e)
        reply_message(event, TextSendMessage(text='エラーが発生しました'))


@handler.add(PostbackEvent)
def handle_postback(event):
    print("postbackEvent", event)

    if event.postback.data:

        person_id = event.postback.data
        print(person_id)

        r = redis.from_url(settings.REDIS_URL)
        rcache = r.get(person_id)

        if not rcache:
            return

        data = json.loads(rcache.decode())
        print(data)

        images = data.get('images')

        image_urls = []
        for image_url in images:
            if image_url.startswith('https://'):
                image_urls.append(image_url)

        print(image_urls)

        if not len(image_urls):
            return

        columns = [
            ImageCarouselColumn(
                image_url=image_url,
                action=URIAction(
                    label='画像出典元',
                    uri=image_url,
                )
            )
            for image_url in image_urls
        ]

        messages = TemplateSendMessage(
            alt_text='template',
            template=CarouselTemplate(columns=columns),
        )

        reply_message(event, messages)


def reply_message(event, messages):
    print(event.reply_token)
    print(messages)
    line_bot_api.reply_message(
        event.reply_token,
        messages=messages,
    )
