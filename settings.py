# coding: UTF-8

import os
from os.path import dirname, join

from dotenv import load_dotenv


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

REDIS_URL = os.environ.get('REDIS_URL')

DEVELOPER_KEY = os.environ.get('DEVELOPER_KEY')
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
GNAVI_API_KEY = os.environ.get('GNAVI_API_KEY')
HOTPEPPER_API_KEY = os.environ.get('HOTPEPPER_API_KEY')

# Azure
CUSTOM_VISION_PREDICTION_KEY_DRINKEE = os.environ.get(
    'CUSTOM_VISION_PREDICTION_KEY_DRINKEE')
CUSTOM_VISION_PROJECT_ID_DRINKEE = os.environ.get(
    'CUSTOM_VISION_PROJECT_ID_DRINKEE')

FACE_API_KEY = os.environ.get('FACE_API_KEY')

# LINE
DRINKEE_CHANNEL_ACCESS_TOKEN = os.environ.get('DRINKEE_CHANNEL_ACCESS_TOKEN')
DRINKEE_CHANNEL_SECRET = os.environ.get('DRINKEE_CHANNEL_SECRET')
