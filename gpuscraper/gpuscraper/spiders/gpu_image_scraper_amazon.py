import time

import scrapy
import queue
import sqlite3

from ..items import GpuImgItem

from fuzzywuzzy import process

class GpuImgScraper(scrapy.Spider):
    name = "gpu_imgs_amazon"
    custom_settings = {
        # 'DOWNLOAD_DELAY': 3,
        'ITEM_PIPELINES': {
            "gpuscraper.pipelines.GpuImgScraperPipeline": 400
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

    def start_requests(self):
        while not self.gpu_names_q.empty():
            search_query = self.gpu_names_q.get()
            gpu_name = self.gpu_names_from_db.get()
            self.urls.append({"url": f"https://www.amazon.co.uk/s?k={search_query}",
                         "search_query": search_query,
                         "gpu_name": gpu_name})

        for url in self.urls:
            yield scrapy.Request(url["url"], self.parse, cb_kwargs={"search_query": url["search_query"],
                                                              "gpu_name": url["gpu_name"]})


    def parse(self, response, search_query, gpu_name):
        items = GpuImgItem()
        gpu_dict = {}

        gpu_containers = response.xpath("//div[@data-component-type='s-search-result']//div[@class='a-section']")[:12]

        # Now gpu_containers only contains non-sponsored containers
        gpu_containers = [container for container in gpu_containers if not self.is_sponsored(container)]

        # gpu_containers_gpu_names = []
        # gpu_containers_gpu_images = []
        # gpu_containers_gpu_prices = []

        for container in gpu_containers:
            name = container.xpath(".//span[@class='a-size-medium a-color-base a-text-normal']/text()").get()
            image = container.xpath(".//img/@src").get()
            price = container.xpath(".//span[@class='a-price']/span[@class='a-offscreen']/text()").get()

            # gpu_containers_gpu_names.append(name)
            # gpu_containers_gpu_images.append(image)
            # gpu_containers_gpu_prices.append(price)

            gpu_dict[name] = {"image": image, "price": price}

        #print(gpu_containers_gpu_names)

        # gpu_containers_gpu_names = response.xpath("//div[@data-component-type='s-search-result']//span[@class='a-size-medium a-color-base a-text-normal']/text()").getall()[:12]
        # gpu_containers_gpu_names = response.xpath("//span[@class='a-size-medium a-color-base a-text-normal']/text()").getall()

        #gpu_container_gpu_images = response.xpath("//div[@data-component-type='s-search-result']//img/@src").getall()[:12]

        #gpu_container_gpu_prices = response.xpath("//div[@data-component-type='s-search-result']//span[@class='a-price']/span[@class='a-offscreen']/text()").getall()[:12]

        # gpu_dict[gpu_containers_gpu_names] = {"image": gpu_container_gpu_images, "price": gpu_container_gpu_prices}

        # for name, image, price in zip(gpu_containers_gpu_names, gpu_containers_gpu_images, gpu_containers_gpu_prices):
        #     gpu_dict[name] = {"image": image, "price": price}


        best_match, score = process.extractOne(search_query, gpu_dict.keys())
        print(f"GPU Name in DB: {gpu_name}")
        print(f"Score: {score}")

        if score < 86:
            items["gpu_name"] = gpu_name
            items["img_url"] = "https://static.vecteezy.com/system/resources/previews/014/987/440/original/motherboard-gpu-icon-simple-computer-card-vector.jpg"
            items["price"] = "N/A"
        else:
            best_match_container = gpu_dict.get(best_match)

            items["gpu_name"] = gpu_name
            items["img_url"] = best_match_container["image"]
            items["price"] = best_match_container["price"]

        # best_match_container = gpu_dict.get(best_match)
        #
        # items["gpu_name"] = gpu_name
        # items["img_url"] = best_match_container["image"]
        # items["price"] = best_match_container["price"]

        # items["gpu_name"] = gpu_name
        # items["img_url"] = gpu_dict[gpu_containers_gpu_names]["image"]
        # items["price"] = gpu_dict[gpu_containers_gpu_names]["price"]

        yield items








if __name__ == "__main__":
   pass

