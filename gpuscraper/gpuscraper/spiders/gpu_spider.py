import time
import re
import scrapy
from scrapy.exceptions import CloseSpider
from selenium.webdriver.support.wait import WebDriverWait

from ..items import GpuscraperItem
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

def select_manufacturer(manufacturer):
    element = driver.find_element(By.ID, "mfgr")
    select = Select(element)
    select.select_by_value(manufacturer)
    print("Selected", manufacturer)

def deselect_manufacturer():
    element = driver.find_element(By.ID, "mfgr")
    select = Select(element)
    select.select_by_index(0)
    print("Deselected manufacturer")

def set_mobile(select_value):
    element = driver.find_element(By.ID, "mobile")
    select = Select(element)
    select.select_by_value(select_value.capitalize())

def set_workstation(select_value):
    element = driver.find_element(By.ID, "workstation")
    select = Select(element)
    select.select_by_value(select_value.capitalize())

def get_bus_interface_option_values():
    element = driver.find_element(By.ID, "interface")
    select = Select(element)
    option_elements = select.options
    option_values = [option.get_attribute("value") for option in option_elements]


    return option_values
def get_all_PCIe_interface_values():
    element = driver.find_element(By.ID, "interface")
    select = Select(element)
    option_elements = select.options
    option_values = []

    for option in option_elements:
        if option.get_attribute("value").startswith("PCIe"):
            option_values.append(option.get_attribute("value"))

    return option_values

def get_all_release_date_values():
    element = driver.find_element(By.ID, "released")
    option_values = element.find_elements(By.TAG_NAME, "option")

    release_date_values = []

    for dates in option_values:
        release_date_values.append(dates.get_attribute("value"))

    return release_date_values

def set_release_date(release_date):
    element = driver.find_element(By.ID, "released")
    select = Select(element)
    select.select_by_value(release_date)

def reset_release_date_form():
    element = driver.find_element(By.ID, "released")
    select = Select(element)
    select.select_by_index(0)

def set_bus_interface(select_value):
    element = driver.find_element(By.ID, "interface")
    select = Select(element)
    select.select_by_value(select_value)


def reset_bus_interface():
    element = driver.find_element(By.ID, "interface")
    select = Select(element)
    select.select_by_index(0)

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
    #Bus interface values have an empty space encoding added as they are going to be passed as a value to change the url
    PCIe_values = ["PCIe%202.0%20x16", "PCIe%203.0%20x16", "PCIe%203.0%20x8", "PCIe%204.0%20x4", "PCIe%204.0%20x8"]
    contains_PCIe_values = True
    manufacturer_index = 0
    PCIe_value_index = 0
    #https://www.techpowerup.com/gpu-specs/?mfgr=AMD&mobile=No&workstation=No&sort=name
    #start_urls = ["https://www.techpowerup.com/gpu-specs/?mobile=No&workstation=No&sort=name"]
    #start_urls = ["https://www.techpowerup.com/gpu-specs/?mfgr=AMD&mobile=No&workstation=No&sort=name"]
    #start_urls = ["https://www.techpowerup.com/gpu-specs/?mfgr=AMD&mobile=No&workstation=No&interface=PCIe%202.0%20x16&sort=name"]

    def start_requests(self):
        for m in self.manufacturers:
            for pci in self.PCIe_values:
                request = scrapy.Request(
                    f"https://www.techpowerup.com/gpu-specs/?mfgr={m}&mobile=No&workstation=No&interface={pci}&sort=name",
                    callback=self.parse,
                    cb_kwargs={"manufacturer": m}
                )

                yield request
                time.sleep(10)

    def parse(self, response, manufacturer):
        items = GpuscraperItem()
        driver.get(response.url)

        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//table[@class='processors']")))

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

        # for value in PCIe_values:
        #     time.sleep(2)
        #     set_bus_interface(value)
        #     #driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        #     WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//table[@class='processors']")))
        #     time.sleep(5)
        #     gpus_tbody = response.xpath("//table[@class='processors']/tr").getall()
        #     time.sleep(5)
        #     cleaned_gpus_tbody = [remove_tr_tags(gpu_values) for gpu_values in gpus_tbody]

            # for gpus in cleaned_gpus_tbody:
            #     split_gpu_values = split_td_tags(gpus)
            #     items["brand"] = "AMD"
            #     items["name"] = extract_a_contents(split_gpu_values[0])
            #     items["clock_speed"] = split_gpu_values[5]
            #     #memory_values = split_memory_string(split_gpu_values[4])
            #     items["memory"] = split_gpu_values[4]
            #     # items["memory_size"] = memory_values[0]
            #     # items["memory_type"] = memory_values[1]
            #     items["memory_speed"] = split_gpu_values[6]
            #     #items["bus_width"] = memory_values[2]

            # for gpus in cleaned_gpus_tbody:
            #     split_gpu_values = split_td_tags(gpus)
            #
            #     items["brand"] = "AMD"
            #     items["name"] = extract_a_contents(split_gpu_values[0])
            #     items["clock_speed"] = split_gpu_values[5]
            #     items["memory"] = split_gpu_values[4]
            #     items["memory_speed"] = split_gpu_values[6]
            #
            #     yield items
            #
            # reset_bus_interface()


    # def parse(self, response):
    #     items = GpuscraperItem()
    #
    #     driver.get(response.url)
    #     #PCI_values = get_all_PCI_interface_values()
    #
    #
    #     for man in self.manufacturers:
    #         #PCI_values_index = 0
    #         time.sleep(5)
    #         select_manufacturer(man)
    #         time.sleep(2)
    #         release_dates = get_all_release_date_values()
    #         time.sleep(2)
    #         for date in release_dates:
    #             #set_bus_interface(pci)
    #             time.sleep(3)
    #             set_release_date(date)
    #             WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//table[@class='processors']")))
    #             driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #
    #             gpus_tbody = response.xpath("//table[@class='processors']/tr").getall()
    #             cleaned_gpus_tbody = [remove_tr_tags(gpu_values) for gpu_values in gpus_tbody]
    #
    #             for gpus in cleaned_gpus_tbody:
    #                 split_gpu_values = split_td_tags(gpus)
    #                 items["brand"] = man
    #                 items["name"] = extract_a_contents(split_gpu_values[0])
    #                 items["clock_speed"] = split_gpu_values[5]
    #                 #memory_values = split_memory_string(split_gpu_values[4])
    #                 items["memory"] = split_gpu_values[4]
    #                 # items["memory_size"] = memory_values[0]
    #                 # items["memory_type"] = memory_values[1]
    #                 items["memory_speed"] = split_gpu_values[6]
    #                 #items["bus_width"] = memory_values[2]
    #
    #                 yield items
    #
    #             time.sleep(2)
    #             reset_release_date_form()
    #             #reset_bus_interface()
    #             time.sleep(2)
    #             #PCI_values_index += 1
    #
    #         deselect_manufacturer()
    #         time.sleep(2)
    #         reset_release_date_form()
    #         #reset_bus_interface()
    #         time.sleep(2)

    def check(self, response):
        driver.get(response.url)
        i = response.xpath("//table[@class='processors']/tr").getall()
        c = [remove_tr_tags(gpu_values) for gpu_values in i]

        print("URL before changing any options:", response.url)
        #print(f"Before selecting manufacturer: {c}")

        select_manufacturer("AMD")
        time.sleep(3)
        set_bus_interface("PCIe 2.0 x16")
        time.sleep(3)

        g = response.xpath("//table[@class='processors']/tr").getall()
        f = [remove_tr_tags(gpu_values) for gpu_values in g]

        print("URL after changing any options:", response.url)
        #print(f"After selecting manufacturer: {f}")

    def closed(self, reason):
        # Close the WebDriver when the spider is closed
        driver.quit()