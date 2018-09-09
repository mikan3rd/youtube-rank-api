import itertools
import re
import urllib.parse
from datetime import datetime
from pprint import pprint
from time import sleep

from bs4 import BeautifulSoup
from functional import seq
from langdetect import detect_langs
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.keys import Keys
from settings import (
    DRIVER_PATH,
    GOOGLE_CHROME_PATH,
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
    hashtag_list = sorted(hashtag_list, key=lambda k: k.get('num', 0) or 0, reverse=True)
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

        print("new:", count)
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

                    languages = []
                    if re.search(r'[ぁ-んァ-ン]+', text) is not None:
                        languages = ['ja']

                    elif re.search(r'[一-龥]+', text) is not None:
                        languages = ['ja', 'zh']

                    # try:
                    #     detect_list = detect_langs(text)
                    #     languages = [detect.lang for detect in detect_list]

                    # except Exception as e:
                    #     languages = []

                    # 日本語を含まないものはスキップ
                    if 'ja' not in languages:
                        continue

                    results.append({
                        'name': text,
                        'page': '%s-%s' % (x + 1, y),
                        'languages': ','.join(languages),
                        'update_at': now,
                    })

            except Exception as e:
                pprint(e)
                break

    except Exception as e:
        # pprint(e)
        pass

    finally:
        driver.quit()

    print("results:", len(results))
    return results


def get_hashtag_detail(driver, hashtag_name):
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    result = {}

    try:
        encode_hashtag = urllib.parse.quote(hashtag_name)
        url = "/explore/tags/%s/" % (encode_hashtag)
        print("get_hashtag_detail:", hashtag_name)

        driver.get(BASE_URL + url)
        sleep(5)
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, "lxml")

        main_tag = soup.find("main")
        header_tag = main_tag.find("header")
        article_tag = main_tag.find("article")

        img_tag = header_tag.find("img")
        span_tag = header_tag.find("span")
        span_tag_inner = span_tag.find("span")
        num = int(span_tag_inner.text.replace(",", ""))

        img_tag_list = article_tag.find_all("img")

        hashtag_set = set()
        for img in img_tag_list:
            alt = img.get("alt")

            if not alt:
                continue

            hashtag_set |= set(get_tag(alt))

        result = {
            'icon': '=IMAGE("%s")' % (img_tag.get('src', no_image_url)),
            'num': num,
            'url': BASE_URL + url,
            'update_at': now,
            'hashtag_set': hashtag_set,
        }

    except Exception as e:
        pprint(e)

    return result


def get_location_japan():
    response = gspread.get_sheet_values(SHEET_ID_INSTAGRAM, "city", "FORMULA")
    label_list, city_list = gspread.convert_to_dict_data(response)
    city_names = {city.get('city') for city in city_list}

    url = "/explore/locations/JP/"
    print(url)

    num = 1
    while True:
        try:
            driver = get_driver()
            page = '?page=%s' % (num)
            print("page:", num)
            driver.get(BASE_URL + url + page)
            sleep(1)
            html_source = driver.page_source
            soup = BeautifulSoup(html_source, "lxml")

            main_tag = soup.find("main")
            list_tags = main_tag.find_all("li")
            for li in list_tags:
                a_tag = li.find("a")

                if not a_tag:
                    continue

                city = a_tag.text
                if city in city_names:
                    continue

                city_list.append({
                    'city': city,
                    'page': num,
                    'href': a_tag.get('href'),
                })
                print("NEW!", city)

            num += 1

        except Exception as e:
            pprint(e)
            break

        finally:
            driver.quit()

    body = {'values': gspread.convert_to_sheet_values(label_list, city_list)}
    gspread.update_sheet_values(SHEET_ID_INSTAGRAM, 'city', body)
    print("SUCCESS!! get_location_japan")


def get_spots():
    response = gspread.get_sheet_values(SHEET_ID_INSTAGRAM, "city", "FORMULA")
    _, city_list = gspread.convert_to_dict_data(response)

    response = gspread.get_sheet_values(SHEET_ID_INSTAGRAM, "spot", "FORMULA")
    label_list, spot_list = gspread.convert_to_dict_data(response)
    spot_names = {spot.get('spot') for spot in spot_list}

    for city in city_list:
        num = 1
        new_num = 0
        while True:
            try:
                driver = get_driver()
                page = '?page=%s' % (num)
                print(page)
                driver.get(BASE_URL + city['href'] + page)
                sleep(1)
                html_source = driver.page_source
                soup = BeautifulSoup(html_source, "lxml")

                main_tag = soup.find("main")
                list_tags = main_tag.find_all("li")
                for li in list_tags:
                    a_tag = li.find("a")

                    if not a_tag:
                        continue

                    spot = a_tag.text
                    if spot in spot_names:
                        continue

                    spot_list.append({
                        'city': city['city'],
                        'spot': spot,
                        'page': num,
                        'href': a_tag.get('href'),
                    })
                    print("NEW!", spot)
                    new_num += 1

                num += 1

            except Exception as e:
                pprint(e)
                break

            finally:
                driver.quit()

        print("NEW", new_num)
        values = gspread.convert_to_sheet_values(label_list, spot_list)
        body = {'values': values}
        gspread.update_sheet_values(SHEET_ID_INSTAGRAM, 'spot', body)

    print("SUCCESS!! get_spots")


def get_tag(text):
    ''' インスタグラムのハッシュタグを取得する
    ルールは`#で始まり、_を除く記号で終わる部分`
    備考: インスタグラムのハッシュタグルールでは、全角の記号は含まれない
    ex.) #abc？edfという文字列では、"abc"のみがハッシュタグとなる
    ただしどの文字が対象であるかがどこにもなく、これをフォローすることが難しいため、
    このメソッドでは全角記号には現状は対応しない。従って以下の結果となる
    ex.) #abc？edfという文字列では、"abc？edf"をハッシュタグとして返却する
    '''
    pattern = r'#([\S]+?)(?=[ -\/:-@\[-^\`\{-\~])|#([\S]+?)(?=$)'
    matches = list(
        seq(re.finditer(pattern, text, re.MULTILINE | re.DOTALL))
        .map(lambda match: [match.group(1), match.group(2)])
        .flatten()
        .filter(lambda match: match)
    )
    return matches


def add_hashtag_list():
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
        print("LOGIN FINISH!!")

        response = gspread.get_sheet_values(SHEET_ID_INSTAGRAM, "hashtag", "FORMULA")
        label_list, hashtag_list = gspread.convert_to_dict_data(response)

        count = 1
        new_num = 0
        for index, hashtag in enumerate(hashtag_list[:5]):

            # 進行状況を表示
            if index % 100 == 0:
                print("index:", index)

            # 100件ごとに保存する
            if count % 100 == 0:
                body = {'values': gspread.convert_to_sheet_values(label_list, hashtag_list)}
                gspread.update_sheet_values(SHEET_ID_INSTAGRAM, 'hashtag', body)
                print("count:", count)

            if 'ja' not in hashtag['languages']:
                continue

            data = get_hashtag_detail(driver, hashtag['name'])
            hashtag_set = data.get('hashtag_set', set())

            for new_tag in hashtag_set:

                find = next((index for hashtag in hashtag_list if hashtag['name'] == new_tag), None)

                if find is not None:
                    continue

                hashtag_list.append({
                    'name': new_tag,
                    'update_at': data.get('update_at'),
                })
                print(new_tag)
                new_num += 1

            count += 1

        hashtag_list = sorted(hashtag_list, key=lambda k: k.get('num', 0) or 0, reverse=True)
        body = {'values': gspread.convert_to_sheet_values(label_list, hashtag_list)}
        gspread.update_sheet_values(SHEET_ID_INSTAGRAM, 'hashtag', body)
        print("new:", new_num)
        print("SUCCESS!! add_hashtag_detail")

    except Exception as e:
        pprint(e)

    finally:
        driver.quit()


def update_languages():
    response = gspread.get_sheet_values(SHEET_ID_INSTAGRAM, "hashtag", "FORMULA")
    label_list, hashtag_list = gspread.convert_to_dict_data(response)

    for index, hashtag in enumerate(hashtag_list):
        name = hashtag['name']
        print(name)

        try:
            detect_list = detect_langs(name)
            languages = [detect.lang for detect in detect_list]
            print(languages)

        except Exception as e:
            print(e)
            continue

        new_data = hashtag_list[index]
        new_data['languages'] = ','.join(languages)
        hashtag_list[index] = new_data

    body = {'values': gspread.convert_to_sheet_values(label_list, hashtag_list)}
    gspread.update_sheet_values(SHEET_ID_INSTAGRAM, 'hashtag', body)
    print("SUCCESS!! update_languages")


def get_driver():
    options = ChromeOptions()
    options.binary_location = GOOGLE_CHROME_PATH
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = Chrome(executable_path=DRIVER_PATH, chrome_options=options)
    driver.set_page_load_timeout(10)
    driver.set_script_timeout(10)
    driver.implicitly_wait(10)
    return driver
