import time

import scrapy
import queue
import sqlite3

from scrapy import signals
from selenium.webdriver import Keys

#from ..items import GpuPriceItem

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

service = webdriver.ChromeService(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

class GpuPriceScraper(scrapy.Spider):
    name = "gpu_prices"
    custom_settings = {
        'ITEM_PIPELINES': {
            "gpuscraper.pipelines.GpuPriceScraperPipeline": 400
        }
    }
    # https://www.google.com/search?q=AMD&tbm=shop
    def __init__(self, *args, **kwargs):
        super(GpuPriceScraper, self).__init__()
        self.search_queue = self.search_query_queue()
        self.gpu_names = self.get_gpu_names()
        # self.gpu_urls = []
        # self.actions = ActionChains(driver)
        # # Variable not in use, only left for testing purposes
        # self.i = 0

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

    def search_query_queue(self):
        q = queue.Queue()

        conn = sqlite3.connect("../gpus.db")
        curr = conn.cursor()

        curr.execute("""select brand from gpus_tb""")
        gpu_brand_names = curr.fetchall()
        curr.execute("""select name from gpus_tb""")
        gpu_names = curr.fetchall()
        curr.execute("""select memory from gpus_tb""")
        memory_specs = curr.fetchall()
        conn.close()

        for brand, name, memory in zip(gpu_brand_names, gpu_names, memory_specs):
            q.put(brand[0] + " " + name[0] + " " + memory[0])

        return q

    def start_requests(self):
        while not self.search_queue.empty():
            query = self.search_queue.get()
            gpu_name = self.gpu_names.get()

            yield scrapy.Request(f"https://www.google.com/search?q={query}&tbm=shop",
                                 self.parse,
                                 cb_kwargs={"gpu_name": gpu_name})

    def parse(self, response, gpu_name):
        pass

if __name__ == "__main__":
    driver.get("https://www.google.com/search?q=AMD Radeon RX 7600 XT 16 GB, GDDR6, 128 bit&tbm=shop")
    i = driver.find_element(By.XPATH, "//div")
    time.sleep(5000)