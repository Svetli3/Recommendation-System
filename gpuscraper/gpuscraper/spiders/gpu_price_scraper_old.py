import random
import time

import scrapy
import queue
import sqlite3
import json

from scrapy import signals
from selenium.webdriver import Keys

from ..items import GpuPriceItem

from fuzzywuzzy import process

import undetected_chromedriver as uc
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from selenium_stealth import stealth

options = webdriver.ChromeOptions()
# Adding argument to disable the AutomationControlled flag
options.add_argument("--disable-blink-features=AutomationControlled")
# Exclude the collection of enable-automation switches
options.add_experimental_option("excludeSwitches", ["enable-automation"])
# Turn-off userAutomationExtension
options.add_experimental_option("useAutomationExtension", False)
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.3")
options.add_argument("--disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument("--disable-automation")
# options.add_argument("--headless")

# !!!!!! UNCOMMENT PART BELOW TO RUN CODE !!!!!!
#
# service = webdriver.ChromeService(ChromeDriverManager().install())
# driver = webdriver.Chrome(service=service)

# stealth(driver,
#         user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
#         languages="en-GB,en-US;q=0.9,en;q=0.8,bg;q=0.7",
#         vendor="Google Inc.",
#         platform="Win32",
#         webgl_vendor="Intel Inc.",
#         renderer="Intel Iris OpenGL Engine",
#         fix_hairline=True
# )

class GpuPriceScraper(scrapy.Spider):
    name = "gpu_prices_old"
    custom_settings = {
        'ITEM_PIPELINES': {
            "gpuscraper.pipelines.GpuPriceScraperPipeline": 400
        }
    }

    def __init__(self, *args, **kwargs):
        super(GpuPriceScraper, self).__init__()
        self.gpu_names = self.gpu_names_queue()
        self.gpu_names_from_db = self.get_gpu_names()
        self.actions = ActionChains(driver)
        self.gpus_from_search_results = []
        self.best_match_gpu_names = []
        # Variable not in use, only left for testing purposes
        self.i = 0

    def get_gpu_names(self):
        q = queue.Queue()

        conn = sqlite3.connect("../gpus.db")
        curr = conn.cursor()

        curr.execute("""select name from gpus_tb""")
        gpu_names = curr.fetchall()

        conn.close()

        for name in gpu_names:
            q.put(name[0])

        return q

    def gpu_names_queue(self):
        q = queue.Queue()

        conn = sqlite3.connect("../gpus.db")
        curr = conn.cursor()

        curr.execute("""select brand from gpus_tb""")
        gpu_brand_names = curr.fetchall()
        curr.execute("""select name from gpus_tb""")
        gpu_names = curr.fetchall()
        conn.close()

        for brand, name in zip(gpu_brand_names, gpu_names):
            q.put(brand[0] + " " + name[0])

        return q

    def solve_captcha(self):
        time.sleep(5)

        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it(
                (By.XPATH, "//body[@class='no-js']/div/div/div[1]/div/div/iframe")))

        captcha_checkbox = driver.find_element(By.XPATH, "/html/body/div/div/div[1]/div/label/input")
        time.sleep(random.uniform(0.5, 2))  # Adding a random delay before clicking
        captcha_checkbox.click()

        driver.switch_to.default_content()

    def agree_to_privacy_preferences(self):
        time.sleep(3)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='qc-cmp2-container']")))

        privacy_form_buttons = driver.find_element(By.XPATH, "//div[@class='qc-cmp2-summary-buttons']")
        agree_button = privacy_form_buttons.find_element(By.XPATH, "//button[2]")
        agree_button.click()



    def start_requests(self):
        while not self.gpu_names.empty():
            search_query = self.gpu_names.get()

            driver.get(f"https://uk.camelcamelcamel.com")

            self.agree_to_privacy_preferences()

            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='input-group']/input")))
            input_box = driver.find_element(By.XPATH, "//div[@class='input-group']/input")
            input_box.send_keys(search_query)

            time.sleep(3)

            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='input-group-button']/button")))
            input_search_button = driver.find_element(By.XPATH, "//div[@class='input-group-button']/button")
            input_search_button.click()

            self.solve_captcha()

            time.sleep(5)

            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='page']")))

            gpu_grid_cells = driver.find_elements(By.XPATH, "//div[@class='grid-x grid-margin-x search_results']/div")

            for cell in gpu_grid_cells:
                # Locate the div containing the GPU name within the current cell
                gpu_name_div = cell.find_element(By.XPATH, ".//div/p/strong/a")
                # Retrieve the GPU name text
                gpu_name = gpu_name_div.text
                # print(gpu_name)

                gpu_price_table = cell.find_element(By.XPATH, ".//div/table/tbody")
                gpu_price = gpu_price_table.find_element(By.XPATH, ".//tr/td[2]/span").text

                self.gpus_from_search_results.append({"gpu_name": gpu_name,
                                                      "gpu_name_from_db": self.gpu_names_from_db.get(),
                                                      "price": gpu_price}
                                                     )

            # print(gpus_from_search_results)
            # Extract GPU names from gpu_list
            gpu_names = [gpu["gpu_name"] for gpu in self.gpus_from_search_results]

            # Find the best match for the search query
            best_match, similarity_score = process.extractOne(search_query, gpu_names)
            self.best_match_gpu_names.append(best_match)

            time.sleep(7)

            # Retrieve GPU name, price, and Amazon link
            # matched_gpu_name = best_match_dict["gpu_name"]
            # matched_price = best_match_dict["price"]
            # matched_amazon_link = best_match_dict["amazon_link"]
            #
            # print("Best Match GPU Name:", matched_gpu_name)
            # print("Price:", matched_price)
            # print("Amazon Link:", matched_amazon_link)
            # print("Similarity Score:", similarity_score)

        with open("best_match_gpu_names.txt", "w") as f:
            for name in self.best_match_gpu_names:
                f.write(name + "\n")

        for result in self.gpus_from_search_results:
            scrapy.Request("", self.parse, cb_kwargs={"gpu_name": result["gpu_name_from_db"], "price": result["price"]})


    def parse(self, response, gpu_name, price):
        items = GpuPriceItem()
        print("gpu_name:", gpu_name)
        print("price:", price)
        items["gpu_name"] = gpu_name
        items["price"] = price

        yield items

        # driver.get(f"https://www.google.com/search?q={search_query}")

        # time.sleep(5)
        #
        # images_button = driver.find_element(By.CLASS_NAME, "LatpMc nPDzT T3FoJb")
        # images_button.click()
        #
        # time.sleep(5)

    # def closed(self, reason):
    #     # Close the WebDriver when the spider is closed
    #     driver.quit()


if __name__ == "__main__":
    pass
    # def gradual_scroll(driver, element):
    #     """
    #     Gradually scrolls the webpage to bring the specified element into view.
    #     """
    #     # Get the initial scroll position
    #     initial_scroll_position = driver.execute_script("return window.pageYOffset;")
    #
    #     # Get the target element's position
    #     target_element_position = element.location_once_scrolled_into_view['y']
    #
    #     # Calculate the distance to scroll
    #     distance_to_scroll = target_element_position - initial_scroll_position
    #
    #     # Set the number of steps and the delay between each step
    #     num_steps = 100  # Adjust as needed
    #     delay_between_steps = 0.1  # Adjust as needed
    #
    #     # Calculate the distance to scroll in each step
    #     step_distance = distance_to_scroll / num_steps
    #
    #     # Gradually scroll in increments
    #     for i in range(num_steps):
    #         scroll_distance = step_distance * (i + 1)
    #         driver.execute_script("window.scrollBy(0, arguments[0]);", scroll_distance)
    #         time.sleep(delay_between_steps)
    #
    #     finished_scroll = True
    #
    #     return finished_scroll
    #
    # g = GpuImgScraper()
    # n = g.get_gpu_names_and_memory_speeds()
    #
    # search_query = "GeForce RTX 3070 Ti 8 GB GA102"
    # gpus_from_search_results = []
    #
    # driver.get(f"https://uk.camelcamelcamel.com/search?sq={search_query}")
    #
    # initial_window_handle = driver.window_handles[0]
    #
    # time.sleep(5)
    #
    # WebDriverWait(driver, 20).until(
    #     EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//body[@class='no-js']/div/div/div[1]/div/div/iframe")))
    #
    # captcha_checkbox = driver.find_element(By.XPATH, "/html/body/div/div/div[1]/div/label/input")
    # captcha_checkbox.click()
    #
    # driver.switch_to.default_content()
    #
    # WebDriverWait(driver, 15).until(
    #     EC.presence_of_element_located((By.XPATH, "//div[@id='qc-cmp2-container']")))
    #
    # time.sleep(6)
    # privacy_form_buttons = driver.find_element(By.XPATH, "//div[@class='qc-cmp2-summary-buttons']")
    # agree_button = privacy_form_buttons.find_element(By.XPATH, "//button[2]")
    # agree_button.click()
    #
    # WebDriverWait(driver, 15).until(
    #     EC.presence_of_element_located((By.XPATH, "//div[@id='page']")))
    #
    # gpu_grid_cells = driver.find_elements(By.XPATH, "//div[@class='grid-x grid-margin-x search_results']/div")
    #
    # for cell in gpu_grid_cells:
    #     # Locate the div containing the GPU name within the current cell
    #     gpu_name_div = cell.find_element(By.XPATH, ".//div/p/strong/a")
    #     # Retrieve the GPU name text
    #     gpu_name = gpu_name_div.text
    #     #print(gpu_name)
    #
    #     gpu_price_table = cell.find_element(By.XPATH, ".//div/table/tbody")
    #     gpu_price = gpu_price_table.find_element(By.XPATH, ".//tr/td[2]/span").text
    #
    #     amazon_link = cell.find_element(By.XPATH, ".//div/div[2]/p[3]/a")
    #     #print(amazon_link.text)
    #
    #     gpus_from_search_results.append({"gpu_name": gpu_name, "price": gpu_price, "amazon_link": amazon_link})
    #
    # #print(gpus_from_search_results)
    # # Extract GPU names from gpu_list
    # gpu_names = [gpu["gpu_name"] for gpu in gpus_from_search_results]
    #
    # # Find the best match for the search query
    # best_match, similarity_score = process.extractOne(search_query, gpu_names)
    #
    # # Get the dictionary corresponding to the best match
    # best_match_dict = next(item for item in gpus_from_search_results if item["gpu_name"] == best_match)
    # matched_amazon_link = best_match_dict["amazon_link"]

    # Retrieve GPU name, price, and Amazon link
    # matched_gpu_name = best_match_dict["gpu_name"]
    # matched_price = best_match_dict["price"]
    # matched_amazon_link = best_match_dict["amazon_link"]
    #
    # print("Best Match GPU Name:", matched_gpu_name)
    # print("Price:", matched_price)
    # print("Amazon Link:", matched_amazon_link)
    # print("Similarity Score:", similarity_score)