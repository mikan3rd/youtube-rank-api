
import requests


ACCESS_TOKEN = "Bearer b97a1dffcfb6379f649c3f8f71b17bd6b5d77250"
BASE_URL = "https://qiita.com/api/v2"
headers = {'Authorization': ACCESS_TOKEN}

qiita_url = "https://qiita.com/"
twitter_url = "https://twitter.com"
facebook_url = "https://www.facebook.com"
github_url = "https://github.com"
linkedin_url = "https://www.linkedin.com/"

sheet_id = "1uUjxlXGJxGDJnYWJc6-8TDy4ajzXgfV6acM7l4ht6BI"
no_image_url = "https://upload.wikimedia.org/wikipedia/ja/b/b5/Noimage_image.png"


def patch_item(item_id, title, body, tags):
    url = "/items/%s" % (item_id)
    print(BASE_URL + url)

    headers['Content-Type'] = 'application/json'
    data = {
        'title': title,
        'body': body,
        'tags': tags,
        'tweet': False,
        'gist': False,
        'private': False,
    }
    # print(data)
    response = requests.patch(BASE_URL + url, headers=headers, json=data)
    data = response.json()
    return data
