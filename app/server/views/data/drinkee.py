from io import BytesIO

import settings
from flask import Blueprint, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    ConfirmTemplate,
    ImageMessage,
    MessageEvent,
    PostbackAction,
    PostbackEvent,
    TemplateSendMessage,
    TextMessage,
    TextSendMessage
)

from app.server.helpers.custom_vision import post_predict_image


api_bp = Blueprint('drinkee_api', __name__)


line_bot_api = LineBotApi(settings.DRINKEE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.DRINKEE_CHANNEL_SECRET)

CUSTOM_VISION_PREDICTION_KEY_DRINKEE = settings.CUSTOM_VISION_PREDICTION_KEY_DRINKEE
CUSTOM_VISION_PROJECT_ID_DRINKEE = settings.CUSTOM_VISION_PROJECT_ID_DRINKEE


@api_bp.route("/drinkee/line", methods=['POST'])
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

    result = post_predict_image(
        CUSTOM_VISION_PROJECT_ID_DRINKEE,
        CUSTOM_VISION_PREDICTION_KEY_DRINKEE,
        image=image,
    )

    confirm_template_message = TemplateSendMessage(
        alt_text='Confirm template',
        template=ConfirmTemplate(
            text='画像を学習させますか?',
            actions=[
                PostbackAction(
                    label='YES',
                    display_text='YES',
                    data='yes',
                ),
                PostbackAction(
                    label='NO',
                    display_text='NO',
                    data='no',
                )
            ]
        )
    )

    messages = [
        TextSendMessage(text=result),
        confirm_template_message,
    ]

    reply_message(event, messages)


@handler.add(PostbackEvent)
def handle_postback(event):
    print("postbackEvent", event)

    messages = [
        TextSendMessage(text='postback: %s' % (event.postback.data)),
    ]
    reply_message(event, messages)


def reply_message(event, messages):
    line_bot_api.reply_message(
        event.reply_token,
        messages=messages,
    )
