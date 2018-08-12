import json
import random
from copy import deepcopy
from io import BytesIO
from pprint import pprint

import redis
import requests
from flask import Blueprint, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    ImageMessage,
    MessageEvent,
    PostbackAction,
    PostbackEvent,
    TextMessage,
    TextSendMessage
)
from settings import (
    AV_SOMMELIER_ACCESS_TOKEN,
    AV_SOMMELIER_CHANNEL_SECRET,
    REDIS_URL
)

from app.server.helpers import dmm, face, gspread


api_bp = Blueprint('av_sommelier_api', __name__)


line_bot_api = LineBotApi(AV_SOMMELIER_ACCESS_TOKEN)
handler = WebhookHandler(AV_SOMMELIER_CHANNEL_SECRET)

SHEET_ID = "1i9IqlJa3lCpNkWBm7_XnYG3QGCbfbQkfzhLk_bFI-rU"

reply_endpoint = "https://api.line.me/v2/bot/message/reply"
no_image_url = "https://upload.wikimedia.org/wikipedia/ja/b/b5/Noimage_image.png"
dmm_unit_quey = "/n1=DgRJTglEBQ4GpoD6,YyI,qs_"
EXPIRE = 60 * 60 * 3


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

    if text.startswith('http'):
        send_face_detect(event, image_url=text)
        return

    keyword_list = text.split()
    if len(keyword_list) > 1:
        send_video_list(event, keyword_list)
        return

    person_list = get_sheet_values_list('av_sommelier')
    image_list = get_sheet_values_list('av_sommelier_images')

    results = []
    for person in person_list:

        if text == person['name']:
            results.insert(0, person)
            continue

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

    flex_message = create_flex_message(results, image_list, '"%s"の検索結果' % (text))
    messages.append(flex_message)

    response = reply_raw_message(event, messages)
    if response:
        pprint(response)
        pprint(results[:10])

    # except Exception as e:
    #     pprint(e)
    #     reply_message(event, messages=TextSendMessage(text='エラーが発生しました'))


@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):

    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)
    image = BytesIO(message_content.content)

    send_face_detect(event=event, image=image)


def reply_raw_message(event, messages):
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
    ).json()

    return response


def get_sheet_values_list(sheet_name):
    r = redis.from_url(REDIS_URL)
    rcache = r.get(sheet_name)

    if rcache:
        print("cache HIT!! %s" % (sheet_name))
        person_list = json.loads(rcache.decode())

    else:
        response = gspread.get_sheet_values(SHEET_ID, sheet_name)
        person_label_list, person_list = gspread.convert_to_dict_data(response)
        r.set(sheet_name, json.dumps(person_list), ex=EXPIRE)

    return person_list


def send_face_detect(event, image=None, image_url=None):

    try:
        detect_results = face.get_face_detect(image=image, image_url=image_url)

        if isinstance(detect_results, str):
            reply_message(event, TextSendMessage(text=detect_results))
            return

        identify_results = face.get_face_identify(
            face_ids=[detect_results[0]['faceId']],
            person_group_id="av_sommelier",
        )

        if isinstance(identify_results, str):
            reply_message(event, TextSendMessage(text=identify_results))
            return

        # results = identify_results[0]
        # candidates = results['candidates']

        if len(identify_results) == 0:
            reply_message(event, TextSendMessage(text='似ている顔が見つかりませんでした'))
            return

        results = []
        person_list = get_sheet_values_list('av_sommelier')
        for result in identify_results:
            for candidate in result['candidates']:
                person_id = candidate['personId']
                person = next((person for person in person_list if person['person_id'] == person_id), None)
                if person:
                    person.update({'confidence': candidate['confidence']})
                    results.append(person)

        if len(results) == 0:
            reply_message(event, TextSendMessage(text='似ている顔が見つかりませんでした'))
            return

        image_list = get_sheet_values_list('av_sommelier_images')
        flex_message = create_flex_message(results, image_list, '似ている顔を見つけました')
        messages = [flex_message]
        response = reply_raw_message(event, messages)

        if response:
            pprint(response)
            pprint(results[:10])

    except Exception as e:
        print("error:", e)
        reply_message(event, TextSendMessage(text='エラーが発生しました'))


def create_flex_message(results, image_list, alt_text):
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
                "flex": 4
            }]
        }

        if person.get('height'):
            content = deepcopy(body_content_base)
            content['contents'][0]['text'] = "身長"
            content['contents'][1]['text'] = "%scm" % (person.get('height', ' '))
            body_contents.append(content)

        if person.get('cup'):
            content = deepcopy(body_content_base)
            content['contents'][0]['text'] = "カップ"
            content['contents'][1]['text'] = person.get('cup', ' ')
            body_contents.append(content)

        if person.get('measurements'):
            content = deepcopy(body_content_base)
            content['contents'][0]['text'] = "サイズ"
            content['contents'][1]['text'] = person.get('measurements', ' ')
            body_contents.append(content)

        if person.get('birthday'):
            content = deepcopy(body_content_base)
            content['contents'][0]['text'] = "誕生日"
            content['contents'][1]['text'] = person.get('birthday', ' ')
            body_contents.append(content)

        if person.get('prefectures'):
            content = deepcopy(body_content_base)
            content['contents'][0]['text'] = "出身地"
            content['contents'][1]['text'] = person.get('prefectures',  ' ')
            body_contents.append(content)

        if person.get('hobby'):
            content = deepcopy(body_content_base)
            content['contents'][0]['text'] = "趣味"
            content['contents'][1]['text'] = person.get('hobby',  ' ')
            body_contents.append(content)

        if len(body_contents) == 0:
            content = deepcopy(body_content_base)
            content['contents'][0]['text'] = "情報"
            content['contents'][1]['text'] = 'なし'
            body_contents.append(content)

        confidence = ' '
        if person.get('confidence'):
            confidence = str(round(person['confidence'] * 100, 2)) + '%'

        body = {
            "type": "box",
            "layout": "vertical",
            "contents": [{
                "type": "text",
                "text": person['name_ruby'] if person.get('name_ruby') else ' ',
                "size": "xxs",
                "wrap": True
            }, {
                "type": "text",
                "text": person['name'],
                "size": "xl",
                "weight": "bold"
            }, {
                "type": "text",
                "text": confidence,
                "size": "md"
            }, {
                "type": "box",
                "layout": "vertical",
                "margin": "lg",
                "spacing": "sm",
                "contents": body_contents
            }]
        }

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
                    "uri": person.get('dmm_affiliate_url') or image_url,
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
        "altText": alt_text,
        "contents": {
            "type": "carousel",
            "contents": flex_list,
        },
        # "quickReply": {
        #     "items": [
        #         {
        #             "type": "action",
        #             "action": {
        #                 "type": "message",
        #                 "label": "Sushi",
        #                 "text": "Sushi"
        #             }
        #         },
        #         {
        #             "type": "action",
        #             "action": {
        #                 "type": "message",
        #                 "label": "Tempura",
        #                 "text": "Tempura"
        #             }
        #         },
        #         {
        #             "type": "action",
        #             "action": {
        #                 "type": "location",
        #                 "label": "Send location"
        #             }
        #         }
        #     ]
        # }
    }

    return flex_message


def send_video_list(event, keyword_list):
    response = dmm.search_items(keyword=' '.join(keyword_list), hits=10)
    result = response['result']
    item_list = result['items']
    total_count = result['total_count']

    if len(item_list) == 0:
        reply_message(event, TextSendMessage(text='該当する動画が見つかりませんでした'))
        return

    messages = []
    messages.append({
        "type": "text",
        "text": "%s件の動画が見つかりました" % (total_count)
    })

    if total_count > 10:
        messages.append({
            "type": "text",
            "text": "最初の10件を表示します"
        })

    flex_list = []
    for item in item_list[:10]:

        image = item.get('imageURL')
        if image:
            image_url = image.get('large') or no_image_url

        else:
            image_url = no_image_url

        body_contents = [{
            "type": "text",
            "text": item.get('title'),
            "weight": "bold",
            "wrap": True,
            "size": "md"
        }]

        if item.get('review'):
            review_list = []
            average = round(float(item['review']['average']))

            for i in range(5):
                review_star = {
                    "type": "icon",
                    "size": "sm",
                    "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gray_star_28.png"
                }
                if average >= i + 1:
                    review_star['url'] = "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"

                review_list.append(review_star)

            review_text = {
                "type": "text",
                "text": item['review']['average'],
                "size": "sm",
                "color": "#999999",
                "margin": "md",
                "flex": 0
            }

            review_list.append(review_text)

            review_content = {
                "type": "box",
                "layout": "baseline",
                "margin": "md",
                "contents": review_list,
            }

            body_contents.append(review_content)

        item_info = item.get('iteminfo')
        if item_info:
            content_list = []
            item_label_list = [
                {'label': 'genre', 'name': 'ジャンル'},
                {'label': 'actress', 'name': '女優'},
                {'label': 'maker', 'name': 'メーカー'},
                {'label': 'director', 'name': '監督'},
                {'label': 'sampleMovie', 'name': 'サンプル'}
            ]
            for label in item_label_list:
                label_ascii = label.get('label')
                if label_ascii == 'sampleMovie':
                    label_content = 'あり' if item.get('sampleMovieURL') else 'なし'

                else:
                    label_content_list = item_info.get(label_ascii, [])
                    label_content_name_list = []
                    for content in label_content_list:
                        _id = content.get('id')
                        if isinstance(_id, str):
                            continue
                        name = content.get('name')
                        if name:
                            label_content_name_list.append(name)

                    if len(label_content_name_list) == 0:
                        continue

                    label_content = '\n'.join(label_content_name_list[:10])

                base_content = {
                    "type": "box",
                    "layout": "baseline",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "text",
                            "text": label.get('name'),
                            "color": "#aaaaaa",
                            "size": "sm",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": label_content,
                            "wrap": True,
                            "color": "#666666",
                            "size": "sm",
                            "flex": 3
                        }
                    ]
                }

                content_list.append(base_content)

            item_content = {
                "type": "box",
                "layout": "vertical",
                "margin": "lg",
                "spacing": "sm",
                "contents": content_list,
            }
            body_contents.append(item_content)

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
                    "uri": item.get('affiliateURL') or image_url,
                }
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": body_contents,
            },
            "footer": {
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
                            "label": "詳細を見る",
                            "uri": item.get('affiliateURL') or image_url
                        }
                    }
                ]
            }
        }

        flex_list.append(bubble_container)

    # pprint(flex_list)
    # return

    flex_message = {
        "type": "flex",
        "altText": '%sの検索結果' % (' '.join(keyword_list)),
        "contents": {
            "type": "carousel",
            "contents": flex_list,
        },
    }

    messages.append(flex_message)
    response = reply_raw_message(event, messages)

    if response:
        pprint(response)


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
