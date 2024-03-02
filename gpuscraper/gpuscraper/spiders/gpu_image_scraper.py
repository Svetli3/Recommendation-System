import time

import scrapy
import queue
import sqlite3

from scrapy import signals
from selenium.webdriver import Keys

#from ..items import GpuImgItem

from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


PATH = "C:\Program Files (x86)\chromedriver.exe"

service = Service(executable_path=PATH)
driver = webdriver.Chrome(service=service)

class GpuImgScraper(scrapy.Spider):
    name = "gpu_imgs"
    def __init__(self, *args, **kwargs):
        super(GpuImgScraper, self).__init__()
        self.gpu_names = self.gpu_names_queue()

    def gpu_names_queue(self):
        q = queue.Queue()

        conn = sqlite3.connect("C:/Users/svetl/PycharmProjects/Recommendation-System/gpuscraper/gpus.db")
        curr = conn.cursor()

        curr.execute("""select brand from gpus_tb""")
        gpu_brand_names = curr.fetchall()
        curr.execute("""select name from gpus_tb""")
        gpu_names = curr.fetchall()
        conn.close()

        for brand, name in zip(gpu_brand_names, gpu_names):
            q.put(brand[0] + " " + name[0])

        return q

    def start_requests(self):
        while not self.gpu_names.empty():
            search_query = self.gpu_names.get()
            driver.get(f"https://www.google.com/search?q={search_query}&tbm=isch")

            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//div[@class='islrc']")))
            parent_div_images = driver.find_element(By.XPATH, "//div[@class='islrc']")
            image_divs = parent_div_images.find_elements(By.CLASS_NAME, "isv-r PNCib ViTmJb BUooTd")[1:16]


        # yield scrapy.Request(f"https://www.google.com/search?q={search_query}&tbm=isch",
        #                      callback=self.parse,
        #                      cb_kwargs={"search_query": search_query})

    def parse(self, response, search_query):
        print("Search query:", search_query)
        time.sleep(5)

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
    q = GpuImgScraper()
    actions = ActionChains(driver)
    search_query = q.gpu_names.get()
    driver.get(f"https://www.google.com/search?q={search_query}&tbm=isch")

    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@id='islrg']/div[@class='islrc']")))
    parent_div_images = driver.find_element(By.XPATH, "//div[@id='islrg']/div[@class='islrc']")
    image_divs = parent_div_images.find_elements(By.XPATH, ".//*")[1:6]

    image_divs_a_tags = []
    for div in image_divs:
        a = div.find_element(By.XPATH, "//a[@class='FRuiCf islib nfEiy']")
        image_divs_a_tags.append(a)

    for i in image_divs_a_tags:
        i.click()
        time.sleep(3)

        image_popup = driver.find_element(By.XPATH, "//a[@class='jlTjKd']")
        actions.move_to_element(image_popup).perform()

        resolution_span_tag = image_popup.find_element(By.XPATH, "//span[@class='qhktO']")

        # index 0 = width, index 3 = height
        # Beware of &nbsp in span tag text, will mess up split of string
        image_resolution = resolution_span_tag.text.split()

        if int(image_resolution[0]) < 1200 and int(image_resolution[2]) < 840:
            continue
        else:
            pass
            #scrapy.Request("", self.parse)

    driver.close()

