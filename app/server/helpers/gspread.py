import base64
from datetime import datetime
from pprint import pprint

import oauth2client.client
from apiclient.discovery import build
from settings import GOOGLE_CLIENT_EMAIL, GOOGLE_PRIVATE_KEY


SCOPES = 'https://www.googleapis.com/auth/spreadsheets'


def get_sheet_values(sheet_id, _range, render='FORMATTED_VALUE'):
    credentials = get_credentials()
    service = build('sheets', 'v4', credentials=credentials)
    response = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=_range,
        valueRenderOption=render,
    ).execute()
    return response


def update_sheet_values(sheet_id, _range, body):
    credentials = get_credentials()
    service = build('sheets', 'v4', credentials=credentials)
    response = service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=_range,
        body=body,
        valueInputOption='USER_ENTERED'
    ).execute()
    pprint(response)
    return response


def convert_to_dict_data(response):
    raw_sheet_data = response['values']
    label_list = raw_sheet_data.pop(0)

    results = []
    for sheet in raw_sheet_data:
        result = {}
        for index, label in enumerate(label_list):
            if not label:
                continue

            if index > len(sheet) - 1:
                continue

            value = sheet[index]
            if label in ['rank_num', 'trend_num', 'followers_count', 'num']:
                try:
                    value = int(value)
                except Exception as e:
                    pass
            result[label] = value
        results.append(result)

    return label_list, results


def convert_to_sheet_values(label_list, data_list):
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    values = [label_list]
    for data in data_list:
        cells = []

        for index, label in enumerate(label_list):

            # if label == 'update_at':
            #     cells.append(now)
            #     continue

            if label == 'create_at' and not data.get(label):
                cells.append(now)
                continue

            cells.append(data.get(label, ''))

        values.append(cells)

    return values


def get_credentials():
    # 環境変数で読み込むと"\n"が改行文字として認識されないため
    private_key = GOOGLE_PRIVATE_KEY.replace("\\n", "\n")

    credentials = oauth2client.client \
        .SignedJwtAssertionCredentials(
            GOOGLE_CLIENT_EMAIL,
            private_key,
            scope=SCOPES,
        )
    return credentials
