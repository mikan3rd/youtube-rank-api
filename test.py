# from langdetect import detect, detect_langs

from app.tasks import instagram


if __name__ == '__main__':
    # instagram.update_hashtag()
    instagram.update_languages()

    # text = "單眼皮手寫歌單"
    # print(text)

    # result = detect(text)
    # print(result)

    # results = detect_langs(text)
    # print(results)

    # for res in results:
    #     print(res.lang)
