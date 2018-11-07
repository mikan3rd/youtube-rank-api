# coding: UTF-8

import os
from os.path import dirname, join

from dotenv import load_dotenv


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

REDIS_URL = os.environ.get('REDIS_URL')
DRIVER_PATH = os.environ.get('DRIVER_PATH')

# Google
DEVELOPER_KEY = os.environ.get('DEVELOPER_KEY')
GOOGLE_CLIENT_EMAIL = os.environ.get('GOOGLE_CLIENT_EMAIL')
GOOGLE_PRIVATE_KEY = os.environ.get('GOOGLE_PRIVATE_KEY')
GOOGLE_TIKTOK_CLIENT_EMAIL = os.environ.get('GOOGLE_TIKTOK_CLIENT_EMAIL')
GOOGLE_TIKTOK_PRIVATE_KEY = os.environ.get('GOOGLE_TIKTOK_PRIVATE_KEY').replace("\\n", "\n")

GOOGLE_CHROME_PATH = os.environ.get('GOOGLE_CHROME_PATH')

STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
GNAVI_API_KEY = os.environ.get('GNAVI_API_KEY')
HOTPEPPER_API_KEY = os.environ.get('HOTPEPPER_API_KEY')

# Azure
CUSTOM_VISION_PREDICTION_KEY_DRINKEE = os.environ.get('CUSTOM_VISION_PREDICTION_KEY_DRINKEE')
CUSTOM_VISION_PROJECT_ID_DRINKEE = os.environ.get('CUSTOM_VISION_PROJECT_ID_DRINKEE')

FACE_API_KEY = os.environ.get('FACE_API_KEY')
MS_COGNINITIVE_API_KEY = os.environ.get('MS_COGNINITIVE_API_KEY')

# LINE
DRINKEE_CHANNEL_ACCESS_TOKEN = os.environ.get('DRINKEE_CHANNEL_ACCESS_TOKEN')
DRINKEE_CHANNEL_SECRET = os.environ.get('DRINKEE_CHANNEL_SECRET')
AV_SOMMELIER_ACCESS_TOKEN = os.environ.get('AV_SOMMELIER_ACCESS_TOKEN')
AV_SOMMELIER_CHANNEL_SECRET = os.environ.get('AV_SOMMELIER_CHANNEL_SECRET')
LINE_OCR_ACCESS_TOKEN = os.environ.get('LINE_OCR_ACCESS_TOKEN')
LINE_OCR_SECRET = os.environ.get('LINE_OCR_SECRET')

# DMM
DMM_API_ID = os.environ.get('DMM_API_ID')
DMM_AFFILIATE_ID = os.environ.get('DMM_AFFILIATE_ID')

# 東京公共交通オープンデータ
ACL_CONSUMERKEY = os.environ.get('ACL_CONSUMERKEY')

# SHEET_ID
SHEET_ID_INSTAGRAM = os.environ.get("SHEET_ID_INSTAGRAM")

# Instagram
INSTAGRAM_USERNAME = os.environ.get("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.environ.get("INSTAGRAM_PASSWORD")

# TIKTOK
TIKTOK_DEVICE_ID = os.environ.get('TIKTOK_DEVICE_ID')
TIKTOK_AID = os.environ.get('TIKTOK_AID')

# Twitter
TWITTER_CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
TWITTER_CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')

TWITTER_GITHUB_ACCESS_TOKEN = os.environ.get('TWITTER_GITHUB_ACCESS_TOKEN')
TWITTER_GITHUB_SECRET = os.environ.get('TWITTER_GITHUB_SECRET')

TWITTER_AV_SOMMLIER_ACCESS_TOKEN = os.environ.get('TWITTER_AV_SOMMLIER_ACCESS_TOKEN')
TWITTER_AV_SOMMLIER_SECRET = os.environ.get('TWITTER_AV_SOMMLIER_SECRET')

TWITTER_AV_ACTRESS_ACCESS_TOKEN = os.environ.get('TWITTER_AV_ACTRESS_ACCESS_TOKEN')
TWITTER_AV_ACTRESS_SECRET = os.environ.get('TWITTER_AV_ACTRESS_SECRET')
