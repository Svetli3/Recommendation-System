import scrapy
import queue
import sqlite3

from ..items import GpuImgItem

from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

PATH = "C:\Program Files (x86)\chromedriver.exe"

service = Service(executable_path=PATH)
driver = webdriver.Chrome(service=service)

def gpu_names_queue():
    q = queue.Queue()

    conn = sqlite3.connect("gpus.db")
    curr = conn.cursor()

    curr.execute("""select name from gpus_tb""")
    gpu_names = curr.fetchall()
    conn.close()

    for name in gpu_names:
        q.put(name)

    return q

class GpuImgScraper(scrapy.Spider):
    name = "gpu_imgs"
    gpu_names = gpu_names_queue()

    def parse(self, response):
        pass