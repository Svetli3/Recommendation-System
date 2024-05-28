import time

import scrapy
import queue
import sqlite3

from ..items import GpuImgItem

from fuzzywuzzy import process

class GpuImgScraper(scrapy.Spider):
    name = "gpu_imgs_amazon"
    custom_settings = {
        'DOWNLOAD_DELAY': 15,
        'CONCURRENT_REQUESTS': 32,
        'ITEM_PIPELINES': {
            "gpuscraper.pipelines.GpuPriceImgScraperPipeline": 400
        }
    }

    def __init__(self, *args, **kwargs):
        super(GpuImgScraper, self).__init__()
        self.urls = []
        self.gpu_names_q = self.gpu_names_queue()
        self.gpu_names_from_db = self.get_gpu_names()
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

    def is_sponsored(self, gpu_container):
        sponsored_tag = gpu_container.xpath(".//span[@class='puis-label-popover-default']").get()

        if sponsored_tag is not None:
            return True
        else:
            return False

    def has_price_tag(self, gpu_container):
        price_tag = gpu_container.xpath(".//span[@class='a-price']").get()

        if price_tag is not None:
            return True
        else:
            return False

    def start_requests(self):
        # Loop until the queue of GPU names is empty
        while not self.gpu_names_q.empty():
            # Get the next GPU search query from the queue
            search_query = self.gpu_names_q.get()
            # Get the corresponding GPU name from the database
            gpu_name = self.gpu_names_from_db.get()
            # Append the URL and related data to the urls list
            self.urls.append({"url": f"https://www.amazon.co.uk/s?k={search_query}",
                         "search_query": search_query,
                         "gpu_name": gpu_name})

        # Yield a request for each URL with the necessary callback arguments
        for url in self.urls:
            yield scrapy.Request(
                url["url"],
                self.parse,
                cb_kwargs={
                    "search_query": url["search_query"],
                    "gpu_name": url["gpu_name"]
                }
            )


    def parse(self, response, search_query, gpu_name):
        # Create an instance to store the scraped item data
        items = GpuImgItem()
        # Dictionary to store GPU data
        gpu_dict = {}

        # Select the first 12 GPU containers from the search results
        gpu_containers = response.xpath("//div[@data-component-type='s-search-result']//div[@class='a-section']")[:12]

        # Filter out sponsored containers
        gpu_containers = [container for container in gpu_containers if not self.is_sponsored(container)]

        # Iterate through the filtered GPU containers
        for container in gpu_containers:
            # Extract the price of the GPU
            price = container.xpath(".//span[@class='a-price']/span[@class='a-offscreen']/text()").get()

            # Check if the container has a price tag
            if self.has_price_tag(container):
                # Extract the name and image URL of the GPU
                name = container.xpath(".//span[@class='a-size-medium a-color-base a-text-normal']/text()").get()
                image = container.xpath(".//img/@src").get()

                # Add the GPU details to the dictionary
                gpu_dict[name] = {"image": image, "price": price}
            else:
                # Skip the container if it doesn't have a price tag
                continue

        # Find the best matching GPU name from the search results
        best_match, score = process.extractOne(search_query, gpu_dict.keys())
        print(f"GPU Name in DB: {gpu_name}")
        print(f"GPU Name in Container: {best_match}")
        print(f"Score: {score}")

        if score < 86:
            # If below threshold, use default values
            items["gpu_name"] = gpu_name
            items["img_url"] = "https://static.vecteezy.com/system/resources/previews/014/987/440/original/motherboard-gpu-icon-simple-computer-card-vector.jpg"
            items["price"] = "N/A"
        else:
            # If above threshold, use the best match data
            best_match_container = gpu_dict.get(best_match)

            items["gpu_name"] = gpu_name
            items["img_url"] = best_match_container["image"]
            items["price"] = best_match_container["price"]

        # Yield the item for further processing
        yield items








if __name__ == "__main__":
   pass