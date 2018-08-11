import json
from io import BytesIO
from pprint import pprint

import redis
from flask import Blueprint, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    CarouselColumn,
    CarouselTemplate,
    FlexContainer,
    FlexSendMessage,
    ImageCarouselColumn,
    ImageCarouselTemplate,
    ImageMessage,
    MessageEvent,
    PostbackAction,
    PostbackEvent,
    TemplateSendMessage,
    TextMessage,
    TextSendMessage,
    URIAction,
    BubbleContainer,
    BoxComponent
)
from settings import AV_SOMMELIER_ACCESS_TOKEN, AV_SOMMELIER_CHANNEL_SECRET

from app.server.helpers import gspread

import requests


# from app.server.helpers.face import get_face_detect, get_face_identify


api_bp = Blueprint('av_sommelier_api', __name__)


line_bot_api = LineBotApi(AV_SOMMELIER_ACCESS_TOKEN)
handler = WebhookHandler(AV_SOMMELIER_CHANNEL_SECRET)

reply_endpoint = "https://api.line.me/v2/bot/message/reply"


@api_bp.route("/line/av_sommelier", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    pprint(body)

    # handle webhook body
    try:
        handler.handle(body, signature)

    except InvalidSignatureError as e:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    print(text)

    # r = redis.from_url(settings.REDIS_URL)

    # columns = [
    #     ImageCarouselColumn(
    #         image_url=image_url,
    #         action=URIAction(
    #             label='画像出典元',
    #             uri=image_url,
    #         )
    #     )
    #     for image_url in image_urls[:10]
    # ]

    # alt_text = 'test'

    # body = BoxComponent()

    # contents = BubbleContainer(body=body)

    # messages = FlexSendMessage(
    #     alt_text=alt_text,
    #     contents=FlexContainer(contents),
    # )

    # reply_message(event, messages)

    messages = [{
        "type": "flex",
        "altText": "this is a flex message",
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "hello"
                    },
                    {
                        "type": "text",
                        "text": "world"
                    }
                ]
            }
        }
    }]

    headers = {
        "Authorization": "Bearer " + AV_SOMMELIER_ACCESS_TOKEN,
        'Content-Type': 'application/json',
    }

    reply_token = event.reply_token
    print("reply_token:", reply_token)

    _json = {
        'replyToken': reply_token,
        'messages': messages,
    }

    response = requests.post(
        reply_endpoint,
        headers=headers,
        json=_json,
    )

    pprint(response.json())


# @handler.add(MessageEvent, message=ImageMessage)
# def handle_image(event):

#     message_id = event.message.id
#     message_content = line_bot_api.get_message_content(message_id)
#     image = BytesIO(message_content.content)

#     try:
#         detect_results = get_face_detect(image=image)

#         if isinstance(detect_results, str):
#             reply_message(event, TextSendMessage(text=detect_results))
#             return

#         identify_results = get_face_identify([detect_results[0]['faceId']])

#         if isinstance(identify_results, str):
#             reply_message(event, TextSendMessage(text=identify_results))
#             return

#         # results = identify_results[0]
#         # candidates = results['candidates']

#         if len(identify_results) == 0:
#             reply_message(event, TextSendMessage(text='似ている顔が見つかりませんでした'))
#             return

#         r = redis.from_url(settings.REDIS_URL)
#         contents = []

#         for result in identify_results:
#             for candidate in result['candidates']:
#                 person_id = candidate['personId']
#                 rcache = r.get(person_id)

#                 if not rcache:
#                     continue

#                 data = json.loads(rcache.decode())

#                 if data.get('times'):
#                     data['times'] += 1

#                 else:
#                     data['times'] = 1

#                 r.set(person_id, json.dumps(data))

#                 content = {
#                     'name': data['name'].strip(),
#                     'image': data.get('images')[0],
#                     'times': data['times'],
#                     'person_id': person_id,
#                     'confidence': candidate['confidence']
#                 }
#                 print(content)
#                 contents.append(content)

#         if len(contents) == 0:
#             reply_message(event, TextSendMessage(text='似ている顔が見つかりませんでした'))
#             return

#         columns = [
#             CarouselColumn(
#                 thumbnail_image_url=content['image'],
#                 title=content['name'],
#                 text='類似度：%s\n検索回数：%s' % (
#                     str(round(content['confidence'] * 100, 2)) + '%',
#                     content['times']
#                 ),
#                 actions=[
#                     PostbackAction(
#                         label='画像をもっと見る',
#                         display_text='画像をもっと見る',
#                         data=person_id,
#                     ),
#                     URIAction(
#                         label='Wikipediaを開く',
#                         uri='%s/%s' % (wiki_url, content['name']),
#                     ),
#                     URIAction(
#                         label='画像出典元',
#                         uri=content['image'],
#                     )
#                 ]
#             )
#             for content in contents[:10]
#         ]

#         messages = TemplateSendMessage(
#             alt_text='似ている顔を見つけました',
#             template=CarouselTemplate(columns=columns),
#         )

#         reply_message(event, messages)

    # except Exception as e:
    #     print("error:", e)
    #     reply_message(event, TextSendMessage(text='エラーが発生しました'))


# @handler.add(PostbackEvent)
# def handle_postback(event):
#     print("postbackEvent", event)

#     if event.postback.data:

#         person_id = event.postback.data

#         r = redis.from_url(settings.REDIS_URL)
#         rcache = r.get(person_id)

#         if not rcache:
#             return

#         data = json.loads(rcache.decode())
#         name = data.get('name')
#         image_urls = data.get('images')

#         if not len(image_urls):
#             return

#         columns = [
#             ImageCarouselColumn(
#                 image_url=image_url,
#                 action=URIAction(
#                     label='画像出典元',
#                     uri=image_url,
#                 )
#             )
#             for image_url in image_urls[:10]
#         ]

#         messages = TemplateSendMessage(
#             alt_text='%sの画像一覧' % (name),
#             template=ImageCarouselTemplate(columns=columns),
#         )

#         reply_message(event, messages)


def reply_message(event, messages):
    line_bot_api.reply_message(
        event.reply_token,
        messages=messages,
    )
