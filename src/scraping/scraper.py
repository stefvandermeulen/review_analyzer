from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class Scraper(object):

    def __init__(self, driver: webdriver=webdriver.Firefox):
        self.driver = driver()
        self.driver.wait = WebDriverWait(self.driver, timeout=2)
        self.driver.maximize_window()

    def go_to_page(self, page: str):

        try:
            self.driver.get(url=page)
        except TimeoutException:
            print("Page {} not found".format(page))

    def lookup(self, query: str):

        assert hasattr(self.driver, "wait")
        try:
            box = self.driver.wait.until(EC.presence_of_element_located(
                (By.NAME, "q")))
            button = self.driver.wait.until(EC.element_to_be_clickable(
                (By.NAME, "btnK")))
            box.send_keys(query)
            button.click()
        except TimeoutException:
            print("Box or Button not found in google.com")
