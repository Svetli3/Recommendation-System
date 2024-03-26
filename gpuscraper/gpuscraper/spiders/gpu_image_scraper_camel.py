import time

import scrapy
import queue
import sqlite3

from scrapy import signals
from selenium.webdriver import Keys

#from ..items import GpuImgItem

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

service = webdriver.ChromeService(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
)

class GpuImgScraper(scrapy.Spider):
    name = "gpu_imgs_google_camel"
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS': 32,
        'ITEM_PIPELINES': {
            "gpuscraper.pipelines.GpuImgScraperPipeline": 400
        }
    }

    def __init__(self, *args, **kwargs):
        super(GpuImgScraper, self).__init__()
        self.gpu_names = self.gpu_names_queue()
        self.gpu_name_and_speed = self.get_gpu_names_and_memory_speeds()
        self.actions = ActionChains(driver)
        # Variable not in use, only left for testing purposes
        self.i = 0

    def get_gpu_names_and_memory_speeds(self):
        q = queue.Queue()

        conn = sqlite3.connect("../../gpus.db")
        curr = conn.cursor()

        curr.execute("""select name from gpus_tb""")
        gpu_names = curr.fetchall()
        curr.execute("""select memory_speed from gpus_tb""")
        memory_speeds = curr.fetchall()
        conn.close()

        for name, memory in zip(gpu_names, memory_speeds):
            q.put( (name[0], memory[0]) )

        return q

    def gpu_names_queue(self):
        q = queue.Queue()

        conn = sqlite3.connect("../../gpus.db")
        curr = conn.cursor()

        curr.execute("""select brand from gpus_tb""")
        gpu_brand_names = curr.fetchall()
        curr.execute("""select name from gpus_tb""")
        gpu_names = curr.fetchall()
        conn.close()

        for brand, name in zip(gpu_brand_names, gpu_names):
            q.put(brand[0] + " " + name[0])

        return q

    def get_best_resolution_url(self, image_urls):
        urls = image_urls["urls"]
        resolutions = image_urls["resolutions"]

        if not resolutions:
            return None  # No resolutions available

            # Find the index of the maximum resolution
        max_index = max(range(len(resolutions)), key=lambda i: resolutions[i][0] * resolutions[i][1])

        if max_index < len(urls):
            return urls[max_index]
        else:
            return None

    def solve_captcha(self):
        time.sleep(5)

        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it(
                (By.XPATH, "//body[@class='no-js']/div/div/div[1]/div/div/iframe")))

        captcha_checkbox = driver.find_element(By.XPATH, "/html/body/div/div/div[1]/div/label/input")
        captcha_checkbox.click()

        driver.switch_to.default_content()

    def agree_to_privacy_preferences(self):
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='qc-cmp2-container']")))

        privacy_form_buttons = driver.find_element(By.XPATH, "//div[@class='qc-cmp2-summary-buttons']")
        agree_button = privacy_form_buttons.find_element(By.XPATH, "//button[2]")
        agree_button.click()

    def start_requests(self):
        while not self.gpu_names.empty():
            search_query = self.gpu_names.get()
            name_and_memory_speed_tuple = self.gpu_name_and_speed.get()

            driver.get(f"https://uk.camelcamelcamel.com/search?sq={search_query}")

            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='page']")))

            gpu_grid_cells = driver.find_elements(By.XPATH, "//div[@class='grid-x grid-margin-x search_results']/div")

            for cell in gpu_grid_cells:
                gpu_name_div = cell.find_elements(By.XPATH, "//div")[1]


    def parse(self, response, img_url, gpu_name, memory_speed):
        items = GpuImgItem()
        print("img_url: ", img_url[:101])
        print("gpu_name:", gpu_name)
        print("memory_speed:", memory_speed)
        items["img_url"] = img_url
        items["gpu_name"] = gpu_name
        items["memory_speed"] = memory_speed

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
    def gradual_scroll(driver, element):
        """
        Gradually scrolls the webpage to bring the specified element into view.
        """
        # Get the initial scroll position
        initial_scroll_position = driver.execute_script("return window.pageYOffset;")

        # Get the target element's position
        target_element_position = element.location_once_scrolled_into_view['y']

        # Calculate the distance to scroll
        distance_to_scroll = target_element_position - initial_scroll_position

        # Set the number of steps and the delay between each step
        num_steps = 100  # Adjust as needed
        delay_between_steps = 0.1  # Adjust as needed

        # Calculate the distance to scroll in each step
        step_distance = distance_to_scroll / num_steps

        # Gradually scroll in increments
        for i in range(num_steps):
            scroll_distance = step_distance * (i + 1)
            driver.execute_script("window.scrollBy(0, arguments[0]);", scroll_distance)
            time.sleep(delay_between_steps)

        finished_scroll = True

        return finished_scroll

    g = GpuImgScraper()
    n = g.get_gpu_names_and_memory_speeds()

    search_query = "GeForce RTX 3070 Ti 8 GB GA102"
    gpus_from_search_results = []

    driver.get(f"https://uk.camelcamelcamel.com/search?sq={search_query}")

    initial_window_handle = driver.window_handles[0]

    time.sleep(5)

    WebDriverWait(driver, 20).until(
        EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//body[@class='no-js']/div/div/div[1]/div/div/iframe")))

    captcha_checkbox = driver.find_element(By.XPATH, "/html/body/div/div/div[1]/div/label/input")
    captcha_checkbox.click()

    driver.switch_to.default_content()

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//div[@id='qc-cmp2-container']")))

    time.sleep(6)
    privacy_form_buttons = driver.find_element(By.XPATH, "//div[@class='qc-cmp2-summary-buttons']")
    agree_button = privacy_form_buttons.find_element(By.XPATH, "//button[2]")
    agree_button.click()

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//div[@id='page']")))

    gpu_grid_cells = driver.find_elements(By.XPATH, "//div[@class='grid-x grid-margin-x search_results']/div")

    for cell in gpu_grid_cells:
        # Locate the div containing the GPU name within the current cell
        gpu_name_div = cell.find_element(By.XPATH, ".//div/p/strong/a")
        # Retrieve the GPU name text
        gpu_name = gpu_name_div.text
        #print(gpu_name)

        gpu_price_table = cell.find_element(By.XPATH, ".//div/table/tbody")
        gpu_price = gpu_price_table.find_element(By.XPATH, ".//tr/td[2]/span").text

        amazon_link = cell.find_element(By.XPATH, ".//div/div[2]/p[3]/a")
        #print(amazon_link.text)

        gpus_from_search_results.append({"gpu_name": gpu_name, "price": gpu_price, "amazon_link": amazon_link})

    #print(gpus_from_search_results)
    # Extract GPU names from gpu_list
    gpu_names = [gpu["gpu_name"] for gpu in gpus_from_search_results]

    # Find the best match for the search query
    best_match, similarity_score = process.extractOne(search_query, gpu_names)

    # Get the dictionary corresponding to the best match
    best_match_dict = next(item for item in gpus_from_search_results if item["gpu_name"] == best_match)
    matched_amazon_link = best_match_dict["amazon_link"]

    # Retrieve GPU name, price, and Amazon link
    # matched_gpu_name = best_match_dict["gpu_name"]
    # matched_price = best_match_dict["price"]
    # matched_amazon_link = best_match_dict["amazon_link"]
    #
    # print("Best Match GPU Name:", matched_gpu_name)
    # print("Price:", matched_price)
    # print("Amazon Link:", matched_amazon_link)
    # print("Similarity Score:", similarity_score)