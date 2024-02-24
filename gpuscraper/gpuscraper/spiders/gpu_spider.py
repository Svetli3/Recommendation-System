import time
import re
import scrapy

from ..items import GpuscraperItem

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

def get_all_PCIe_interface_values():
    element = driver.find_element(By.ID, "interface")
    select = Select(element)
    option_elements = select.options
    option_values = []

    for option in option_elements:
        if option.get_attribute("value").startswith("PCIe"):
            option_values.append(option.get_attribute("value"))

    return option_values

def split_memory_string(memory_string):
    return [value.strip() for value in memory_string.split(",")]

def remove_tr_tags(input_string):
    # Remove <tr> tags, \n, and \t, and keep only <td> tags and their contents
    cleaned_string = re.sub(r'<tr.*?>', '', input_string)  # Remove opening <tr> tag
    cleaned_string = re.sub(r'</tr>', '', cleaned_string)  # Remove closing </tr> tag
    cleaned_string = cleaned_string.replace('\n', '')  # Remove \n
    cleaned_string = cleaned_string.replace('\t', '')  # Remove \t
    return cleaned_string

def split_td_tags(input_string):
    # Use regular expression to find content between <td> and </td> tags
    td_pattern = re.compile(r'<td.*?>(.*?)</td>', re.DOTALL)
    td_contents = td_pattern.findall(input_string)
    return td_contents

def extract_a_contents(input_string):
    # Use regular expression to match content between <a> and </a> tags
    a_pattern = re.compile(r'<a.*?>(.*?)</a>', re.DOTALL)

    # Find the first match in the input string
    match = a_pattern.search(input_string)

    # Extract the content if a match is found
    if match:
        a_contents = match.group(1)
        return a_contents.strip()  # Optional: Remove leading and trailing whitespaces
    else:
        return None

def have_common_elements(array1, array2):
    for element in array1:
        if element in array2:
            return True
    return False
class GpuSpider(scrapy.Spider):
    name = "gpus"
    manufacturers = ["3dfx", "AMD", "ATI", "Intel", "Matrox", "NVIDIA", "Sony", "XGI"]
    PCIe_values = ["PCIe 2.0 x16", "PCIe 3.0 x16", "PCIe 3.0 x8", "PCIe 4.0 x4", "PCIe 4.0 x8"]
    contains_PCIe_values = True
    manufacturer_index = 0
    PCIe_value_index = 0
    #https://www.techpowerup.com/gpu-specs/?mfgr=AMD&mobile=No&workstation=No&sort=name
    #start_urls = ["https://www.techpowerup.com/gpu-specs/?mobile=No&workstation=No&sort=name"]
    #start_urls = ["https://www.techpowerup.com/gpu-specs/?mfgr=AMD&mobile=No&workstation=No&sort=name"]
    #start_urls = ["https://www.techpowerup.com/gpu-specs/?mfgr=AMD&mobile=No&workstation=No&interface=PCIe%202.0%20x16&sort=name"]

    def start_requests(self):
        for m in self.manufacturers:

            driver.get(f"https://www.techpowerup.com/gpu-specs/?mfgr={m}&mobile=No&workstation=No&sort=name")
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//table[@class='processors']")))

            webpage_PCIe_values = get_all_PCIe_interface_values()

            if have_common_elements(self.PCIe_values, webpage_PCIe_values):
                for pci in self.PCIe_values:
                    request = scrapy.Request(
                        f"https://www.techpowerup.com/gpu-specs/?mfgr={m}&mobile=No&workstation=No&interface={pci}&sort=name",
                        callback=self.parse,
                        cb_kwargs={"manufacturer": m}
                    )

                    yield request
            else:
                print(f"{m} does not contain PCIe bus interface values")
                continue

    def parse(self, response, manufacturer):
        items = GpuscraperItem()
        driver.get(response.url)

        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//table[@class='processors']")))
        print(response.url)
        if len(response.xpath("//table[@class='processors']/tr").getall()) == 1:
            pass

        else:
            gpus_tbody = response.xpath("//table[@class='processors']/tr").getall()
            cleaned_gpus_tbody = [remove_tr_tags(gpu_values) for gpu_values in gpus_tbody]

            for gpus in cleaned_gpus_tbody:
                split_gpu_values = split_td_tags(gpus)

                items["brand"] = manufacturer
                items["name"] = extract_a_contents(split_gpu_values[0])
                items["clock_speed"] = split_gpu_values[5]
                items["memory"] = split_gpu_values[4]
                items["memory_speed"] = split_gpu_values[6]

                yield items
    def closed(self, reason):
        # Close the WebDriver when the spider is closed
        driver.quit()