import unittest

from selenium import webdriver

from src.scraping.scraper import Scraper


class ScraperTest(unittest.TestCase):

    def setUp(self):

        self.sc = Scraper(driver=webdriver.Chrome())

    def go_to_page_test(self):

        self.assertTrue(isinstance(self.sc.driver, webdriver.Chrome))
        self.sc.go_to_page(page="https://www.google.com")

    def lookup_test(self):

        self.sc.go_to_page(page="https://www.google.com")
        self.sc.lookup(query="kittens")

        self.fail()


