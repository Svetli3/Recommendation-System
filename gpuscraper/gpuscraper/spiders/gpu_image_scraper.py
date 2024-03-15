import time

import scrapy
import queue
import sqlite3

from scrapy import signals
from selenium.webdriver import Keys

from ..items import GpuImgItem

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

class GpuImgScraper(scrapy.Spider):
    name = "gpu_imgs"
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
        self.gpu_urls = []
        self.actions = ActionChains(driver)
        # Variable not in use, only left for testing purposes
        self.i = 0

    def get_gpu_names_and_memory_speeds(self):
        q = queue.Queue()

        conn = sqlite3.connect("../gpus.db")
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

    def start_requests(self):
        while not self.gpu_names.empty():
            search_query = self.gpu_names.get()
            name_and_memory_speed_tuple = self.gpu_name_and_speed.get()
            image_urls = {"urls": [], "resolutions": []}

            driver.get(f"https://www.google.com/search?q={search_query}&tbm=isch")

            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='islrg']/div[@class='islrc']")))
            gpu_images = driver.find_elements(By.XPATH,
                                              "//div[@id='islrg']/div[@class='islrc']//*/div[@class='fR600b islir']/img")[:5]

            for i in gpu_images:
                try:
                    i.click()
                    # print(i.accessible_name)
                    WebDriverWait(driver, 3).until(EC.presence_of_element_located(
                        (By.XPATH, "//a[@class='jlTjKd']/img[@class='sFlh5c pT0Scc iPVvYb']")))

                    image_popup = driver.find_element(By.XPATH,
                                                      "//a[@class='jlTjKd']/img[@class='sFlh5c pT0Scc iPVvYb']")

                    intrinsic_width = driver.execute_script("return arguments[0].naturalWidth;", image_popup)
                    intrinsic_height = driver.execute_script("return arguments[0].naturalHeight;", image_popup)

                    image_urls["urls"].append(image_popup.get_attribute("src"))
                    image_urls["resolutions"].append((intrinsic_width, intrinsic_height))

                except TimeoutException:
                    continue

            self.gpu_urls.append({"url": self.get_best_resolution_url(image_urls),
                                  "gpu_name": name_and_memory_speed_tuple[0],
                                  "memory_speed": name_and_memory_speed_tuple[1]}
                                 )
            image_urls["urls"] = []
            image_urls["resolutions"] = []

            #self.i += 1

        for url in self.gpu_urls:
            yield scrapy.Request(url["url"],
                                 self.parse,
                                 cb_kwargs={"img_url": url["url"],
                                            "gpu_name": url["gpu_name"],
                                            "memory_speed": url["memory_speed"]
                                            }
                                 )

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
    g = GpuImgScraper()
    n = g.get_gpu_names_and_memory_speeds()

    while not n.empty():
        print(n.get())


    # image_urls = {
    #     "urls": ["url1", "url2", "url3"],
    #     "resolutions": [(1920, 1080), (1280, 720), (3840, 2160)]
    # }
    #
    #
    # def get_best_resolution_url(image_urls):
    #     urls = image_urls["urls"]
    #     resolutions = image_urls["resolutions"]
    #
    #     if not resolutions:
    #         return None  # No resolutions available
    #
    #     # Find the index of the maximum resolution
    #     max_index = max(range(len(resolutions)), key=lambda i: resolutions[i][0] * resolutions[i][1])
    #
    #     if max_index < len(urls):
    #         return urls[max_index]
    #     else:
    #         return None
    #
    #
    # best_resolution_url = get_best_resolution_url(image_urls)
    # print("URL with the best resolution:", best_resolution_url)
