import time
import re
import scrapy

from ..items import GpuscraperItem

from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

# !!!!!! UNCOMMENT PART BELOW TO RUN CODE !!!!!!
#
service = webdriver.ChromeService(ChromeDriverManager().install())
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

def get_manufacturer_and_gpu_name(input_string):
    # Use regular expression to find content between <td> and </td> tags
    td_pattern = re.compile(r'<td class="(.*?)"><a.*?>(.*?)</a></td>', re.DOTALL)
    td_contents = td_pattern.findall(input_string)
    if td_contents:
        manufacturer = td_contents[0][0].split('-')[-1].upper()  # Extracting manufacturer from class attribute
        gpu_name = td_contents[0][1]
        return (manufacturer, gpu_name)  # Returning a tuple of manufacturer and GPU name
    else:
        return (None, None)  # Returning None if no match is found

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
    # Name of the spider
    name = "gpus"

    # Custom settings for the spider
    custom_settings = {
        # Delay between requests to avoid overwhelming the server
        'DOWNLOAD_DELAY': 15,
        # Specify the pipeline for processing scraped items
        'ITEM_PIPELINES': {
            "gpuscraper.pipelines.GpuscraperPipeline": 300
        }
    }

    # List of release dates to scrape data for
    release_dates = ["2024", "2023", "2022", "2021", "2020", "2019", "2018"]

    # Function to generate initial requests based on release dates
    def start_requests(self):
        for date in self.release_dates:
            # Generate a request for each release date URL
            yield scrapy.Request(f"https://www.techpowerup.com/gpu-specs/?released={date}&mobile=No&workstation=No&sort=name",
                                 self.parse
                                 )

    # Function to parse the response from each request
    def parse(self, response):
        # Create an instance to store scraped item data
        items = GpuscraperItem()
        driver.get(response.url)

        # Wait for the table of processors to be present on the page
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//table[@class='processors']")))
        print(response.url)

        # Check if there is only one row (header) in the table
        if len(response.xpath("//table[@class='processors']/tr").getall()) == 1:
            # Skip if no GPU data rows are found
            pass

        else:
            # Extract all rows from the table
            gpus_tbody = response.xpath("//table[@class='processors']/tr").getall()
            # Clean the extracted rows by removing unwanted tags
            cleaned_gpus_tbody = [remove_tr_tags(gpu_values) for gpu_values in gpus_tbody]

            # Iterate through each cleaned row
            for gpus in cleaned_gpus_tbody:
                # Extract manufacturer and GPU name
                manufacturer, gpu_name = get_manufacturer_and_gpu_name(gpus)

                # Split the row data into individual cell values
                split_gpu_values = split_td_tags(gpus)
                # Extract memory details from the cell value
                memory_values = split_memory_string(split_gpu_values[4])
                # Extract clock speed
                clock_speed = split_gpu_values[5]
                # Extract memory info
                memory = split_gpu_values[4]
                # Extract memory speed
                memory_speed = split_gpu_values[6]

                # Skip if the memory type is 'System Shared'
                if memory == "System Shared":
                    continue
                else:
                    # Populate the item fields with scraped data
                    items["brand"] = manufacturer
                    items["name"] = gpu_name
                    items["clock_speed"] = clock_speed
                    items["memory_speed"] = memory_speed
                    items["memory_size"] = memory_values[0]
                    items["memory_type"] = memory_values[1]
                    items["bus_width"] = memory_values[2]

                    yield items
    def closed(self, reason):
        # Close the WebDriver when the spider is closed
        driver.quit()