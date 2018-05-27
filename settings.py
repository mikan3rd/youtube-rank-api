# coding: UTF-8

import os
from os.path import dirname, join

from dotenv import load_dotenv


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

DEVELOPER_KEY = os.environ.get('DEVELOPER_KEY')
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
GNAVI_API_KEY = os.environ.get('GNAVI_API_KEY')
HOTPEPPER_API_KEY = os.environ.get('HOTPEPPER_API_KEY')
