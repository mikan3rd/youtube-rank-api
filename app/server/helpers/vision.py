import requests
from settings import MS_COGNINITIVE_API_KEY


endpoint = 'https://eastasia.api.cognitive.microsoft.com/vision/v1.0/ocr'

image_url = "https://bazubu.com/wp-content/uploads/2013/03/7dec493403292ee13268a2a283d92c151.png"
image_url2 = "https://upload.wikimedia.org/wikipedia/commons/5/57/Lorem_Ipsum_Helvetica.png"
image_url3 = "https://datumstudio.jp/wp-content/uploads/2018/01/pexels-photo-800721-1024x678.jpeg"


def get_text_by_ms(image_url=None, image=None):
    if image_url is None and image is None:
        return '必要な情報が足りません'

    params = {'visualFeatures': 'Categories,Description,Color'}

    if image_url:
        headers = {
            'Ocp-Apim-Subscription-Key': MS_COGNINITIVE_API_KEY,
            'Content-Type': 'application/json',
        }
        data = {'url': image_url}
        response = requests.post(
            endpoint,
            headers=headers,
            params=params,
            json=data
        )

    elif image is not None:
        headers = {
            'Ocp-Apim-Subscription-Key': MS_COGNINITIVE_API_KEY,
            "Content-Type": "application/octet-stream"
        }
        response = requests.post(
            endpoint,
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
    for region in data['regions']:
        for line in region['lines']:
            for word in line['words']:
                text += word.get('text', '')
                if data['language'] != 'ja':
                    text += ' '
        text += '\n'

    if len(text) == 0:
        text += '文字が検出できませんでした'

    print('text:', text)
    return text
