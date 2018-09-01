import itertools
import re
from datetime import datetime
from pprint import pprint
from time import sleep

from bs4 import BeautifulSoup
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.keys import Keys
from settings import (
    DRIVER_PATH,
    GOOGLE_CHROME_BIN,
    INSTAGRAM_PASSWORD,
    INSTAGRAM_USERNAME,
    SHEET_ID_INSTAGRAM
)

from app.server.helpers import gspread


BASE_URL = "https://www.instagram.com"

no_image_url = "https://upload.wikimedia.org/wikipedia/ja/b/b5/Noimage_image.png"

login_url = "https://www.instagram.com/accounts/login/"
loginPath = '//*[@id="react-root"]/section/main/article/div[2]/div[2]/p/a'
usernamePath = '//*[@id="react-root"]/section/main/div/article/div/div/div/form/div[1]/div/div[1]/input'
passwordPath = '//*[@id="react-root"]/section/main/div/article/div/div/div/form/div[2]/div/div[1]/input'


def update_hashtag():
    response = gspread.get_sheet_values(SHEET_ID_INSTAGRAM, "hashtag", "FORMULA")
    label_list, hashtag_list = gspread.convert_to_dict_data(response)

    data = get_hashtag()

    new_num = 0
    for d in data:
        name = d['name']
        index = next((
            index for index, hashtag in enumerate(hashtag_list)
            if hashtag['name'] == name), None)

        if index is None:
            hashtag_list.append(d)
            print("NEW!!:", d.get('page'), d.get('name'))
            new_num += 1
            continue

        new_data = hashtag_list[index]
        new_data.update(d)
        hashtag_list[index] = new_data

    print("new:", new_num)
    body = {'values': gspread.convert_to_sheet_values(label_list, hashtag_list)}
    gspread.update_sheet_values(SHEET_ID_INSTAGRAM, 'hashtag', body)
    print("SUCCESS!! update_hashtag")


def add_hashtag_detail():
    try:
        driver = get_driver()

        # Login
        print("LOGIN START!!")
        driver.get(login_url)

        usernameField = driver.find_element_by_xpath(usernamePath)
        usernameField.send_keys(INSTAGRAM_USERNAME)

        passwordField = driver.find_element_by_xpath(passwordPath)
        passwordField.send_keys(INSTAGRAM_PASSWORD)

        passwordField.send_keys(Keys.RETURN)
        sleep(30)
        print("LOGIN FINISH!!")

        response = gspread.get_sheet_values(SHEET_ID_INSTAGRAM, "hashtag", "FORMULA")
        label_list, hashtag_list = gspread.convert_to_dict_data(response)

        count = 1
        for index, hashtag in enumerate(hashtag_list):

            # 進行状況を表示
            if index % 100 == 0:
                print("index:", index)

            # 100件ごとに保存する
            if count % 100 == 0:
                body = {'values': gspread.convert_to_sheet_values(label_list, hashtag_list)}
                gspread.update_sheet_values(SHEET_ID_INSTAGRAM, 'hashtag', body)
                print("count:", count)

            if hashtag.get('num'):
                continue

            new_hashtag = hashtag
            data = get_hashtag_detail(driver, hashtag['name'])
            new_hashtag.update(data)
            hashtag_list[index] = new_hashtag
            count += 1

        hashtag_list = sorted(hashtag_list, key=lambda k: k.get('num', 0) or 0, reverse=True)
        body = {'values': gspread.convert_to_sheet_values(label_list, hashtag_list)}
        gspread.update_sheet_values(SHEET_ID_INSTAGRAM, 'hashtag', body)
        print("SUCCESS!! add_hashtag_detail")

    except Exception as e:
        pprint(e)

    finally:
        driver.quit()


def get_hashtag():
    X = 40
    Y = 9
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    try:
        driver = get_driver()

        results = []
        for x, y in itertools.product(range(X), range(Y)):

            try:
                url = "/directory/hashtags/%s-%s/" % (x + 1, y)
                print(url)

                driver.get(BASE_URL + url)
                sleep(1)
                html_source = driver.page_source
                soup = BeautifulSoup(html_source, "lxml")
                main_tag = soup.find("main")

                list_tags = main_tag.find_all("li")

                for li in list_tags:
                    a_tag = li.find("a")

                    if not a_tag:
                        continue

                    text = a_tag.text

                    # 英数字 or 日本語 で始まらない場合はスキップ
                    if re.match(r'[a-zA-Z0-9ぁ-んァ-ン一-龥]+', text) is None:
                        continue

                    language = None
                    if re.search(r'[ぁ-んァ-ン]+', text) is not None:
                        language = 'ja'

                    elif re.search(r'[一-龥]+', text) is not None:
                        language = 'ja, zh'

                    # 一旦、日本語を含まないものはスキップ
                    if language is None:
                        continue

                    print(x, y, text)

                    results.append({
                        'name': text,
                        'page': '%s-%s' % (x, y),
                        'language': language,
                        'update_at': now,
                    })

            except Exception as e:
                pprint(e)
                break

    except Exception as e:
        pprint(e)

    finally:
        driver.quit()

    print("results:", len(results))
    return results


def get_hashtag_detail(driver, hashtag_name):
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    result = {}

    try:
        url = "/explore/tags/%s/" % (hashtag_name)
        print(url)

        driver.get(BASE_URL + url)
        sleep(5)
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, "lxml")

        main_tag = soup.find("main")
        header_tag = main_tag.find("header")

        img_tag = header_tag.find("img")
        span_tag = header_tag.find("span")
        span_tag_inner = span_tag.find("span")
        num = int(span_tag_inner.text.replace(",", ""))

        result = {
            'icon': '=IMAGE("%s")' % (img_tag.get('src', no_image_url)),
            'num': num,
            'url': BASE_URL + url,
            'update_at': now,
        }

    except Exception as e:
        pprint(e)

    return result


def get_driver():
    options = ChromeOptions()
    options.binary_location = GOOGLE_CHROME_BIN
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = Chrome(DRIVER_PATH, options=options)
    driver.set_page_load_timeout(10)
    driver.set_script_timeout(10)
    return driver