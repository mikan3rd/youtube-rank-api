import json
import random
from io import BytesIO
from pprint import pprint

import redis
import requests
from flask import Blueprint, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    BoxComponent,
    BubbleContainer,
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
    URIAction
)
from settings import AV_SOMMELIER_ACCESS_TOKEN, AV_SOMMELIER_CHANNEL_SECRET

from app.server.helpers import gspread


# from app.server.helpers.face import get_face_detect, get_face_identify


api_bp = Blueprint('av_sommelier_api', __name__)


line_bot_api = LineBotApi(AV_SOMMELIER_ACCESS_TOKEN)
handler = WebhookHandler(AV_SOMMELIER_CHANNEL_SECRET)

SHEET_ID = "1i9IqlJa3lCpNkWBm7_XnYG3QGCbfbQkfzhLk_bFI-rU"

reply_endpoint = "https://api.line.me/v2/bot/message/reply"
no_image_url = "https://upload.wikimedia.org/wikipedia/ja/b/b5/Noimage_image.png"
dmm_unit_quey = "/n1=DgRJTglEBQ4GpoD6,YyI,qs_"


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

    # try:
    text = event.message.text

    # r = redis.from_url(settings.REDIS_URL)
    # reply_message(event, messages)

    response = gspread.get_sheet_values(SHEET_ID, 'av_sommelier')
    person_label_list, person_list = gspread.convert_to_dict_data(response)

    response = gspread.get_sheet_values(SHEET_ID, 'av_sommelier_images')
    image_label_list, image_list = gspread.convert_to_dict_data(response)

    results = []
    for person in person_list:

        if text in person['name']:
            results.append(person)
            continue

        if text in person['name_ruby']:
            results.append(person)
            continue

    messages = []
    if len(results) == 0:
        results = random.sample(person_list, 10)
        messages.append({
            "type": "text",
            "text": "ランダム"
        })

    else:
        messages.append({
            "type": "text",
            "text": "%s人の名前が見つかりました" % (len(results))
        })

    if len(results) > 10:
        messages.append({
            "type": "text",
            "text": "最初の10件を表示します"
        })

    flex_list = []
    for person in results[:10]:

        name = person['name']
        image = next((image for image in image_list if image['name'] == name), None)

        if not image:
            image_url = no_image_url

        else:
            image_url = image['image_url']

        body_contents = []
        body_content_base = {
            "type": "box",
            "layout": "baseline",
            "spacing": "sm",
            "contents": [{
                "type": "text",
                "text": " ",
                "color": "#aaaaaa",
                "size": "sm",
                "flex": 1
            }, {
                "type": "text",
                "text": " ",
                "wrap": True,
                "color": "#666666",
                "size": "sm",
                "flex": 5
            }]
        }

        if person.get('height'):
            body_content_base['contents'][0]['text'] = "身長"
            body_content_base['contents'][1]['text'] = "%scm" % (person.get('height', ' '))
            body_contents.append(body_content_base)

        if person.get('cup'):
            body_content_base['contents'][0]['text'] = "カップ"
            body_content_base['contents'][1]['text'] = person.get('cup', ' ')
            body_contents.append(body_content_base)

        if person.get('measurements'):
            body_content_base['contents'][0]['text'] = "サイズ"
            body_content_base['contents'][1]['text'] = person.get('measurements', ' ')
            body_contents.append(body_content_base)

        if person.get('birthday'):
            body_content_base['contents'][0]['text'] = "誕生日"
            body_content_base['contents'][1]['text'] = person.get('birthday', ' ')
            body_contents.append(body_content_base)

        if person.get('prefectures'):
            body_content_base['contents'][0]['text'] = "出身地"
            body_content_base['contents'][1]['text'] = person.get('prefectures',  ' ')
            body_contents.append(body_content_base)

        if person.get('hobby'):
            body_content_base['contents'][0]['text'] = "趣味"
            body_content_base['contents'][1]['text'] = person.get('hobby',  ' ')
            body_contents.append(body_content_base)

        body = {
            "type": "box",
            "layout": "vertical",
            "contents": [{
                "type": "text",
                "text": person.get('name_ruby', ' '),
                "size": "xxs",
                "wrap": True
            }, {
                "type": "text",
                "text": person['name'],
                "size": "xl",
                "weight": "bold"
            }, {
                "type": "text",
                "text": " ",
                "size": "md"
            }, {
                "type": "box",
                "layout": "vertical",
                "margin": "lg",
                "spacing": "sm",
                "contents": body_contents
            }]
        },

        bubble_container = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
                "action": {
                    "type": "uri",
                    "uri": image_url,
                }
            },
            "body": body,
        }

        if person.get('dmm_affiliate_url'):
            unit_url = person.get('dmm_affiliate_url').replace("/mikan3rd-990", dmm_unit_quey + "/mikan3rd-990")
            bubble_container['footer'] = {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "color": "#c10100",
                        "action": {
                            "type": "uri",
                            "label": "動画を検索",
                            "uri": person.get('dmm_affiliate_url')
                        }
                    },
                    {
                        "type": "button",
                        "style": "secondary",
                        "action": {
                            "type": "uri",
                            "label": "単体動画を検索",
                            "uri": unit_url
                        }
                    }
                ]
            }

        flex_list.append(bubble_container)

    flex_message = {
        "type": "flex",
        "altText": "%sの検索結果" % (text),
        "contents": {
            "type": "carousel",
            "contents": flex_list,
        }
    }

    messages.append(flex_message)

    headers = {
        "Authorization": "Bearer " + AV_SOMMELIER_ACCESS_TOKEN,
        'Content-Type': 'application/json',
    }

    _json = {
        'replyToken': event.reply_token,
        'messages': messages,
    }

    response = requests.post(
        reply_endpoint,
        headers=headers,
        json=_json,
    )

    pprint(response.json())

    # except Exception as e:
    #     pprint(e)
    #     reply_message(event, messages=TextSendMessage(text='エラーが発生しました'))


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
