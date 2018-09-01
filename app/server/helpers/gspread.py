import os
from datetime import datetime
from pprint import pprint

from apiclient.discovery import build
from oauth2client import client, tools
from oauth2client.file import Storage
from settings import DEVELOPER_KEY


try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'


def get_sheet_values(sheet_id, _range, render='FORMATTED_VALUE'):
    service = build('sheets', 'v4', developerKey=DEVELOPER_KEY)
    response = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=_range,
        valueRenderOption=render,
        key=DEVELOPER_KEY,
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
    print(label_list)

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
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')

    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)

    credential_path = os.path.join(
        credential_dir,
        'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials
