import os
import pathlib
import time

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from dotenv import load_dotenv

load_dotenv(".env")


class Settings:
    BASE_DIR = pathlib.Path(os.getcwd())
    DATA_DIRECTORY = BASE_DIR / 'data'
    VIDEO_DIRECTORY = DATA_DIRECTORY / 'video'
    DRIVER_PATH = BASE_DIR / 'selenium_driver' / 'chromedriver.exe'


class PuzzleEnglishWordScraping:
    SIGNIN_URL = "https://puzzle-english.com/signin"
    GLOSSARY_URL = "https://puzzle-english.com/dictionary?view=cards&item=word"

    def __init__(self, max_pages=None):
        self.max_pages = max_pages
        self.driver = self.__get_driver()

    def _get_options(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        return options

    def __get_driver(self):
        driver = webdriver.Chrome(options=self._get_options())
        # driver.implicitly_wait(time_to_wait=2)
        return driver

    def process(self):
        # Авторизируемся
        self.login()
        self.collect_dictionary()

    def login(self):
        # Авторизируемся
        self.driver.get(self.SIGNIN_URL)
        signin_button = WebDriverWait(self.driver, timeout=10).until(
            expected_conditions.element_to_be_clickable(
                (By.ID, 'alreadyHaveAccount'),
            )
        )
        # signin_button = self.driver.find_element(By.ID, value='alreadyHaveAccount')
        signin_button.click()

        email_field = self.driver.find_element(By.ID, value='email')
        password_field = self.driver.find_element(By.ID, value='password')
        accept_signin_button = self.driver.find_element(By.CLASS_NAME, value='signin-sign-in-form__button')
        email_field.send_keys(os.getenv("PUZZLE_ENGLISH_LOGIN", default=""))
        time.sleep(1)
        password_field.send_keys(os.getenv("PUZZLE_ENGLISH_PASSWORD", default=""))
        accept_signin_button.click()
        time.sleep(10)

    def collect_dictionary(self):
        # Собираем слова

        self.driver.get(self.GLOSSARY_URL)
        word_cards = self.driver.find_elements(by=By.CLASS_NAME, value="puzzle-card")
        # Подготовим новый файл с данными
        data_file = Settings.DATA_DIRECTORY / f"{time.time()}_parse_data.txt"
        with data_file.open(mode='w', encoding='utf-8') as fd:
            for word_card in word_cards:
                word_canvas = word_card.find_element(by=By.CLASS_NAME, value="puzzle-card__head").text.split('\n')
                word_en = word_canvas[0]
                word_ru = word_canvas[1]

                accents_canvas = [item.text for item in
                                  word_card.find_elements(by=By.CLASS_NAME, value="puzzle-card__accents-text")]

                try:
                    video_link = word_card.find_element(by=By.CLASS_NAME, value="card-video-wrap ").get_dom_attribute(
                        name="data-src")
                    r = requests.get(video_link)
                    with (Settings.VIDEO_DIRECTORY / pathlib.Path(video_link).name).open(mode='wb') as video_fd:
                        video_fd.write(r.content)
                except Exception:
                    video_link = 'Нет видео'

                card_phrase_en = word_card.find_element(by=By.CLASS_NAME, value="vocab-card__phrase-eng").text
                card_phrase_ru = word_card.find_element(by=By.CLASS_NAME, value="vocab-card__phrase-rus").text

                data = f"{word_en} {' '.join(accents_canvas)} -> {word_ru}\n{card_phrase_en} {card_phrase_ru}\n{video_link}\n---------------"
                fd.write(data + '\n')
                print(f"Записали {word_en} ({word_ru})")


if __name__ == '__main__':
    PuzzleEnglishWordScraping().process()
    time.sleep(10)
