
import os
import urllib
from pprint import pprint
from time import sleep

from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from settings import DRIVER_PATH, GOOGLE_CHROME_PATH


BASE_URL = 'https://twitter.com'
LOGIN_URL = BASE_URL + '/login'

USERNAME_PATH = '//*[@id="page-container"]/div/div[1]/form/fieldset/div[1]/input'
PASSWORD_PATH = '//*[@id="page-container"]/div/div[1]/form/fieldset/div[2]/input'
PREVIEW_PATH = '//*[@id="timeline"]/div[2]/div/form/div[2]/div[4]/div[1]/div/div[1]/div[%s]'


def post_tweet(
    username,
    password,
    status,
    image_url_list=[],
):
    print(username)
    print(password)
    print(status)
    print(image_url_list)

    try:
        driver = get_driver(username, password)

        tweet = driver.find_element_by_id('tweet-box-home-timeline')
        tweet.send_keys(status)

        path_to_image = os.path.join(os.getcwd(), "tweet_image_%s.jpg")
        print(path_to_image)
        for i, image_url in enumerate(image_url_list, 1):
            image_path = path_to_image % (i)
            urllib.request.urlretrieve(image_url, image_path)
            driver.find_element_by_css_selector('input.file-input').send_keys(image_path)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, PREVIEW_PATH % (i))))
            print('image upload:', i)

        driver.find_element_by_css_selector('button.tweet-action').click()
        sleep(10)

        print("SUCCESS: post_tweet_by_selenium", username)

    except Exception as e:
        pprint(e)

    finally:
        # input()
        # os.remove(path_to_image)
        driver.quit()


def search_and_retweet(
    username,
    password,
    status,
):
    pass


def get_driver(username, password):
    options = ChromeOptions()
    options.binary_location = GOOGLE_CHROME_PATH
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = Chrome(executable_path=DRIVER_PATH, chrome_options=options)
    driver.set_page_load_timeout(10)
    driver.set_script_timeout(10)
    driver.implicitly_wait(10)

    # Login
    driver.get(LOGIN_URL)

    usernameField = driver.find_element_by_xpath(USERNAME_PATH)
    usernameField.send_keys(username)

    passwordField = driver.find_element_by_xpath(PASSWORD_PATH)
    passwordField.send_keys(password)

    passwordField.send_keys(Keys.RETURN)

    print("LOGIN SUCCESS:", username)

    return driver
