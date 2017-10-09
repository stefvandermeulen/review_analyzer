import os
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait

import src.utils.file_manager as fm

from src.scraping.scraper import Scraper
from src.utils.logger import Logger

__author__ = "svdmeulen"


def get_credentials(element: WebElement) -> dict:
    """
    Return the credentials known of the author in the element
    """

    credentials = element.find_elements_by_tag_name("li")
    d = {
        "review-author-name": None,
        "review-author-city": None,
        "review-author-age": None,
        "review-author-date": None
    }
    for credential in credentials:
        variable_name = credential.get_attribute("data-test")
        d[variable_name] = credential.text
    return d


def get_pros_or_cons(element: WebElement, class_name: str) -> list:
    try:
        l = element.find_element_by_class_name(class_name).text.split("\n")
        return l
    except NoSuchElementException as e:
        Logger().info("{} is not an element".format(class_name))

    return ["Unknown"]


def load_more(element: WebElement):

    while True:
        try:
            element.find_element_by_class_name("review-load-more__button").click()
        except Exception as e:
            Logger().info("No more items left")
            break


def main():

    path_output = os.path.join(fm.PATH_HOME, "output")

    scraper = Scraper(driver=webdriver.Chrome)
    scraper.go_to_page(page="https://www.bol.com")

    search_bar = scraper.driver.find_element_by_id("searchfor")
    search_term = "koelkast"
    search_bar.send_keys(search_term)
    search_button = scraper.driver.find_element_by_class_name("input-group__addon")
    search_button.submit()

    parent_element = scraper.driver.find_element_by_class_name("results-area")
    search_results = parent_element.find_elements_by_class_name("product-item--row")

    df = pd.DataFrame()
    for i, search_result in enumerate(search_results):

        if i > 0:
            parent_element = scraper.driver.find_element_by_class_name("results-area")
            search_results = parent_element.find_elements_by_class_name("product-item--row")
            search_result = search_results[i]

        element = search_result.find_element_by_class_name("product-title")
        product_title = element.text
        Logger().info("Processing product {}".format(product_title))

        # Move into product page

        scraper.driver.execute_script("arguments[0].click();", element)

        # element.click()
        # element = search_result.find_element_by_class_name("product-title").click()
        review_section = scraper.driver.find_element_by_class_name("reviews")
        load_more(element=review_section)

        reviews = scraper.driver.find_elements_by_class_name("review")
        Logger().info("Found {} reviews".format(len(reviews)))

        for j, review in enumerate(reviews):
            review_title = review.find_element_by_class_name("review__header").text
            Logger().info("Processing review #{}/{} with review_title '{}'".format(j, len(reviews), review_title))
            product_rating = float(review.find_element_by_name("rating-value").get_attribute("value")) / 100
            parent_element = review.find_element_by_class_name("review-metadata__list")
            credentials = get_credentials(parent_element)
            try:
                recommendation = review.find_element_by_class_name("review-metadata__recommends").text
            except NoSuchElementException:
                Logger().error("No recommendation given")
            pros = get_pros_or_cons(element=review, class_name="review-pros-and-cons__list--pros")
            cons = get_pros_or_cons(element=review, class_name="review-pros-and-cons__list--cons")
            body = review.find_element_by_class_name("review__body").text
            review_feedback_pos = review.find_element_by_class_name("review-feedback__btn--positive").text
            review_feedback_neg = review.find_element_by_class_name("review-feedback__btn--negative").text
            review_feedback_score = int(review_feedback_pos) - int(review_feedback_neg)

            df = df.append(
                pd.DataFrame(
                    {
                        "Product": [search_term],
                        "ProductTitle": [product_title],
                        "ReviewTitle": [review_title],
                        "AuthorName": [credentials["review-author-name"]],
                        "AuthorAge": [credentials["review-author-age"]],
                        "AuthorCity": [credentials["review-author-city"]],
                        "Date": [credentials["review-author-date"]],
                        "ProductRating": [product_rating],
                        "Recommendation": [recommendation],
                        "Pros": [pros],
                        "Cons": [cons],
                        "Notes": [body],
                        "ReviewFeedbackPos": int(review_feedback_pos),
                        "ReviewFeedbackNeg": int(review_feedback_neg),
                        "ReviewFeedbackScore": [review_feedback_score]
                    }
                ), ignore_index=True
            )
        scraper.driver.back()


    fm.write_pandas(df, path=os.path.join(path_output, "{}_review.csv".format(search_term)))


if __name__ == "__main__":
    main()
    print("Complete")
