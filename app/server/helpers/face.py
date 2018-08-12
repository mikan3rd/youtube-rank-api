import requests
import settings


FACE_API_KEY = settings.FACE_API_KEY

endpoint = 'https://eastasia.api.cognitive.microsoft.com/face/v1.0'

person_group_id = "face_search_1"


def get_face_detect(image_url=None, image=None):

    if image_url is None and image is None:
        raise Exception()

    params = {
        'returnFaceId': True,
        'returnFaceLandmarks': False,
        'returnFaceAttributes': 'age',
    }

    if image_url:
        headers = {
            'Ocp-Apim-Subscription-Key': FACE_API_KEY,
            'Content-Type': 'application/json',
        }
        data = {'url': image_url}
        response = requests.post(
            endpoint + '/detect',
            headers=headers,
            params=params,
            json=data
        )

    elif image is not None:
        headers = {
            'Ocp-Apim-Subscription-Key': FACE_API_KEY,
            "Content-Type": "application/octet-stream"
        }
        response = requests.post(
            endpoint + '/detect',
            headers=headers,
            params=params,
            data=image,
        )

    status = response.status_code
    data = response.json()

    if status != 200:
        error = 'エラーが発生しました'

        if status == 429:
            error = '今月に使用できる回数を超過しました'

        elif status == 400:
            if data['code'] == 'InvalidImageSize':
                error = '画像のサイズは1KBから6MBにしてください'

            elif data['code'] == 'InvalidURL':
                error = 'この画像URLからは取得できません'

            elif data['code'] == 'InvalidImage':
                error = '対応していない画像形式です'

        print(status, data)
        return error

    if len(data) == 0:
        return '顔が検知できませんでした'

    return data


def get_face_identify(face_ids, confidenceThreshold=0, person_group_id=person_group_id):

    headers = {
        'Ocp-Apim-Subscription-Key': FACE_API_KEY,
        'Content-Type': 'application/json',
    }

    _json = {
        'faceIds': face_ids[:10],
        'largePersonGroupId': person_group_id,
        'confidenceThreshold': confidenceThreshold,
    }

    res = requests.post(
        endpoint + '/identify',
        headers=headers,
        json=_json,
    )

    status = res.status_code
    data = res.json()

    if status != 200:
        error = 'エラーが発生しました'

        if status == 429:
            error = '今月に使用できる回数を超過しました'

        print(status, data)
        return error

    if len(data) == 0:
        return '似ている顔が見つかりませんでした'

    return data
