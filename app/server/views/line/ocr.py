from io import BytesIO

from flask import Blueprint, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    ImageMessage,
    MessageEvent,
    TextMessage,
    TextSendMessage
)
from settings import LINE_OCR_ACCESS_TOKEN, LINE_OCR_SECRET

from app.server.helpers.vision import get_text_by_ms


line_bot_api = LineBotApi(LINE_OCR_ACCESS_TOKEN)
handler = WebhookHandler(LINE_OCR_SECRET)


api_bp = Blueprint('line_ocr_api', __name__)


@api_bp.route("/line/ocr", methods=['POST'])
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
    print("handle_message:", event)
    text = event.message.text

    if (text.startswith('http')):
        image_text = get_text_by_ms(text)
        messages = [
            TextSendMessage(text=image_text),
        ]

    else:
        messages = [
            TextSendMessage(text=text),
            TextSendMessage(text='画像を送信するか、画像のURLを送ってみてね!'),
        ]

    reply_message(event, messages)


@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    print("handle_image:", event)

    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)

    image = BytesIO(message_content.content)

    try:
        image_text = get_text_by_ms(image=image)

        messages = [
            TextSendMessage(text=image_text),
        ]

        reply_message(event, messages)

    except Exception as e:
        reply_message(event, TextSendMessage(text='エラーが発生しました'))


def reply_message(event, messages):
    line_bot_api.reply_message(
        event.reply_token,
        messages=messages,
    )
