import requests


endpoint = "https://southcentralus.api.cognitive.microsoft.com/customvision/v1.1/Prediction/{projectId}"


def post_predict_image(project_id, prediction_key, image_url=None, image=None):

    if image_url is None and image is None:
        return '必要な情報が足りません'

    params = {'projectId': project_id}

    if image_url:
        headers = {
            'Prediction-key': prediction_key,
            'Content-Type': 'application/json',
        }
        data = {'url': image_url}
        response = requests.post(
            endpoint + '/url',
            headers=headers,
            params=params,
            json=data
        )

    elif image is not None:
        headers = {
            'Prediction-key': prediction_key,
            "Content-Type": "multipart/form-data"
        }
        response = requests.post(
            endpoint + '/image',
            headers=headers,
            params=params,
            data=image,
        )

    status = response.status_code
    data = response.json()

    if status != 200:

        if data['code'] == 'InvalidImageSize':
            text = '画像のサイズが大きすぎます'

        elif data['code'] == 'InvalidImageUrl':
            text = 'この画像URLからは取得できません'

        elif data['code'] == 'InvalidImageFormat':
            text = '対応していない画像形式です'

        else:
            text = 'エラーが発生しました'

        print(status, data)
        return text

    text = ''
    for prediction in data['Predictions']:
        text += 'Tag:' + prediction['Tag'] + '\n'
        text += 'Probability:' + prediction['Probability'] + '\n'
        text += '\n'

    print('text:', text)
    return text
