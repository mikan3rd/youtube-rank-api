from io import BytesIO

import settings
from flask import Blueprint, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    ConfirmTemplate,
    ImageMessage,
    MessageAction,
    MessageEvent,
    PostbackAction,
    PostbackEvent,
    TemplateSendMessage,
    TextMessage,
    TextSendMessage
)


api_bp = Blueprint('drinkee_api', __name__)


line_bot_api = LineBotApi(settings.DRINKEE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.DRINKEE_CHANNEL_SECRET)


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


@handler.add(PostbackEvent, message=TextMessage)
def handle_postback(event):
    print(event)

    messages = [
        TextSendMessage(text='PostBack!'),
    ]
    reply_message(event, messages)


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

    confirm_template_message = TemplateSendMessage(
        alt_text='Confirm template',
        template=ConfirmTemplate(
            text='Are you sure?',
            actions=[
                PostbackAction(
                    label='postback',
                    text='postback text',
                    data='action=buy&itemid=1'
                ),
                MessageAction(
                    label='message',
                    text='message text'
                )
            ]
        )
    )

    reply_message(event, confirm_template_message)


def reply_message(event, messages):
    line_bot_api.reply_message(
        event.reply_token,
        messages=messages,
    )
