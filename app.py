import os
import logging
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
import pytesseract
from PIL import Image
from openai import OpenAI
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)

from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent,
)
from linebot.v3.messaging import MessagingApiBlob

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from flask import Flask


def create_app():
    flask_app = Flask(__name__)

    @flask_app.route("/")
    def home():
        return "OK"

    return flask_app


def extract_text(file_path):
    img = Image.open(file_path)


def extract_text(file_path):
    with open(file_path, "rb") as f:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "この画像から文字をすべて抽出して",
                        },
                        {"type": "input_image", "image": f.read()},
                    ],
                }
            ],
        )
    return response.output_text.strip()


LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")

if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    logger.warning("LINE_CHANNEL_SECRET or LINE_CHANNEL_ACCESS_TOKEN is not set.")

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_message = event.message.text
    reply_text = f"You said: {user_message}"

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)],
            )
        )


@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event):
    print("画像受信きた")

    message_id = event.message.id

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        message_content = MessagingApiBlob(api_client).get_message_content(message_id)

    os.makedirs("images", exist_ok=True)
    file_path = f"images/{message_id}.jpg"

    with open(file_path, "wb") as f:
        f.write(message_content)

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="画像OK")],
            )
        )


def create_app():
    flask_app = Flask(__name__)

    @flask_app.route("/webhook", methods=["POST"])
    def webhook():
        signature = request.headers.get("X-Line-Signature", "")
        body = request.get_data(as_text=True)
        logger.info("Incoming webhook body: %s", body)

        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            logger.error("Invalid signature. Check your channel secret.")
            abort(400)

        return "OK"

    @flask_app.route("/health", methods=["GET"])
    def health():
        return {"status": "ok"}

    @flask_app.route("/__mockup/health", methods=["GET"])
    def health_mock():
        return {"status": "ok"}

    return flask_app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8008)