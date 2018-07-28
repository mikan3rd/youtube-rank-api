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
    ImageCarouselColumn,
    ImageCarouselTemplate
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
    text = event.message.text

    r = redis.from_url(settings.REDIS_URL)
    rcache = r.get(text)

    if not rcache:
        messages = [
            TextSendMessage(text='女性の画像か名前を送ってみてね!'),
        ]
        reply_message(event, messages)
        return

    image_urls = json.loads(rcache.decode())

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
        for image_url in image_urls[:10]
    ]

    messages = TemplateSendMessage(
        alt_text='%sの画像一覧' % (text),
        template=ImageCarouselTemplate(columns=columns),
    )

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

        from pprint import pprint
        pprint(identify_results)
        print()

        if isinstance(identify_results, str):
            reply_message(event, TextSendMessage(text=identify_results))
            return

        # results = identify_results[0]
        # candidates = results['candidates']

        if len(identify_results) == 0:
            reply_message(event, TextSendMessage(text='似ている顔が見つかりませんでした'))
            return

        r = redis.from_url(settings.REDIS_URL)
        contents = []

        for result in identify_results:
            print(result)
            for candidate in result['candidates']:
                person_id = candidate['personId']
                rcache = r.get(person_id)

                if not rcache:
                    continue

                data = json.loads(rcache.decode())

                if data.get('times'):
                    data['times'] += 1

                else:
                    data['times'] = 1

                r.set(person_id, json.dumps(data))

                content = {
                    'name': data.get('name'),
                    'image': data.get('images')[0],
                    'times': data['times'],
                    'person_id': person_id,
                    'confidence': candidate['confidence']
                }
                print(content)
                contents.append(content)

        if len(contents) == 0:
            reply_message(event, TextSendMessage(text='似ている顔が見つかりませんでした'))
            return

        columns = [
            CarouselColumn(
                thumbnail_image_url=content['image'],
                title=content['name'],
                text='類似度：%s\n検索回数：%s' % (
                    str(round(content['confidence'] * 100, 2)) + '%',
                    content['times']
                ),
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
            alt_text='似ている顔を見つけました',
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

        r = redis.from_url(settings.REDIS_URL)
        rcache = r.get(person_id)

        if not rcache:
            return

        data = json.loads(rcache.decode())
        name = data.get('name')
        image_urls = data.get('images')

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
            for image_url in image_urls[:10]
        ]

        messages = TemplateSendMessage(
            alt_text='%sの画像一覧' % (name),
            template=ImageCarouselTemplate(columns=columns),
        )

        reply_message(event, messages)


def reply_message(event, messages):
    print(event.reply_token)
    print(messages)
    line_bot_api.reply_message(
        event.reply_token,
        messages=messages,
    )
