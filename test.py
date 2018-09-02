from polyglot.detect import Detector
from polyglot.text import Text, Word

from app.tasks import instagram


if __name__ == '__main__':
    # instagram.update_hashtag()
    instagram.update_languages()

    # detector = Detector('韓國', quiet=True)
    # print(detector.language.code)
    # for lang in detector.languages:
    #     print(lang)

    # try:
    #     detector = Text("pizza")
    #     print(detector)

    # except Exception as e:
    #     print("ERROR")
