# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class GpuscraperItem(scrapy.Item):
    brand = scrapy.Field()
    name = scrapy.Field()
    clock_speed = scrapy.Field()
    memory = scrapy.Field()
    # memory_size = scrapy.Field()
    memory_speed = scrapy.Field()
    # memory_type = scrapy.Field()
    # bus_width = scrapy.Field()

class GpuImgItem(scrapy.Item):
    gpu_name = scrapy.Field()
    img_url = scrapy.Field()
    price = scrapy.Field()

class GpuPriceItem(scrapy.Item):
    gpu_name = scrapy.Field()
    price = scrapy.Field()