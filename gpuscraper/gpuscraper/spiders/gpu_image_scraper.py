import time

import scrapy
import queue
import sqlite3

from scrapy import signals
from selenium.webdriver import Keys

from ..items import GpuImgItem

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
        self.actions = ActionChains(driver)

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

            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@id='islrg']/div[@class='islrc']")))
            gpu_images = driver.find_elements(By.XPATH,"//div[@id='islrg']/div[@class='islrc']//*/div[@class='fR600b islir']/img")[:5]

            for i in gpu_images:
                i.click()
                #print(i.accessible_name)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[@class='jlTjKd']/img[@class='sFlh5c pT0Scc iPVvYb']")))

                image_popup = driver.find_element(By.XPATH, "//a[@class='jlTjKd']/img[@class='sFlh5c pT0Scc iPVvYb']")
                img_url = image_popup.get_attribute("src")
                intrinsic_width = driver.execute_script("return arguments[0].naturalWidth;", image_popup)
                intrinsic_height = driver.execute_script("return arguments[0].naturalHeight;", image_popup)

                if intrinsic_width < 1200 and intrinsic_height < 840:
                    continue
                else:
                    scrapy.Request(driver.current_url, self.parse, cb_kwargs={"img_url": img_url})

    def parse(self, response, img_url):
        items = GpuImgItem()

        items["img_url"] = img_url

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
    q = GpuImgScraper()
    actions = ActionChains(driver)
    search_query = q.gpu_names.get()
    driver.get(f"https://www.google.com/search?q={search_query}&tbm=isch")

    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@id='islrg']/div[@class='islrc']")))
    gpu_images = driver.find_elements(By.XPATH, "//div[@id='islrg']/div[@class='islrc']//*/div[@class='fR600b islir']/img")[:5]

    for i in gpu_images:
        i.click()
        print(i.accessible_name)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[@class='jlTjKd']/img[@class='sFlh5c pT0Scc iPVvYb']")))

        image_popup = driver.find_element(By.XPATH, "//a[@class='jlTjKd']/img[@class='sFlh5c pT0Scc iPVvYb']")
        intrinsic_width = driver.execute_script("return arguments[0].naturalWidth;", image_popup)
        intrinsic_height = driver.execute_script("return arguments[0].naturalHeight;", image_popup)

        # if intrinsic_width < 1200 and intrinsic_height < 840:
        #     continue
        # else:
        #     scrapy.Request(driver.current_url, self.parse)

    driver.quit()

