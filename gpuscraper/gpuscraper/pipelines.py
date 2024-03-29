# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import sqlite3
# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

class GpuscraperPipeline:

    def __init__(self):
        self.create_connection()
        self.create_table()

    def create_connection(self):
        self.conn = sqlite3.connect("../gpus.db")
        self.curr = self.conn.cursor()

    def create_table(self):
        self.curr.execute("""DROP TABLE IF EXISTS gpus_tb""")
        # self.curr.execute("""create table gpus_tb(
        #                 brand text,
        #                 name text,
        #                 clock_speed text,
        #                 memory_size text,
        #                 memory_speed text,
        #                 memory_type text,
        #                 bus_width text
        #                 )""")
        self.curr.execute("""create table gpus_tb(
                                brand text,
                                name text,
                                clock_speed text,
                                memory text,
                                memory_speed text
                                )""")

    def process_item(self, item, spider):
        self.store_db(item)
        return item

    def store_db(self, item):
        # self.curr.execute("""insert into gpus_tb values (?, ?, ?, ?, ?, ?, ?)""", (
        #     item["brand"],
        #     item["name"],
        #     item["clock_speed"],
        #     item["memory_size"],
        #     item["memory_speed"],
        #     item["memory_type"],
        #     item["bus_width"]
        # ))
        self.curr.execute("""insert into gpus_tb values (?, ?, ?, ?, ?)""", (
            item["brand"],
            item["name"],
            item["clock_speed"],
            item["memory"],
            item["memory_speed"]
        ))
        self.conn.commit()

class GpuImgScraperPipeline:
    def __init__(self):
        self.create_connection()
        self.create_imgs_url_column()
    def create_connection(self):
        self.conn = sqlite3.connect("../gpus.db")
        self.curr = self.conn.cursor()

    def create_imgs_url_column(self):
        is_imgs_url_created = False
        query = "PRAGMA table_info(gpus_tb)"
        self.curr.execute(query)

        columns = self.curr.fetchall()

        for col in columns:
            if col[1] == "imgs_url":
                is_imgs_url_created = True
            else:
                is_imgs_url_created = False

        if is_imgs_url_created:
            print("imgs_url column already created")
        else:
            self.curr.execute("""alter table gpus_tb add imgs_url text""")
            self.conn.commit()
    def store_img_db(self, item):
        self.curr.execute("""update gpus_tb set imgs_url = (?) where name = (?) and memory_speed = (?)""",
                          (item["img_url"], item["gpu_name"], item["memory_speed"]))
        self.conn.commit()

    def process_item(self, item, spider):
        self.store_img_db(item)
        return item

class GpuPriceScraperPipeline:
    def __init__(self):
        self.create_connection()
        self.create_price_column()

    def create_connection(self):
        self.conn = sqlite3.connect("../gpus.db")
        self.curr = self.conn.cursor()

    def create_price_column(self):
        is_price_column_created = False

        query = "PRAGMA table_info(gpus_tb)"
        self.curr.execute(query)

        columns = self.curr.fetchall()

        for col in columns:
            if col[1] == "price":
                is_price_column_created = True
            else:
                is_price_column_created = False

        if is_price_column_created:
            print("price column already created")
        else:
            self.curr.execute("""alter table gpus_tb add price text""")
            self.conn.commit()

    def store_price_db(self, item):
        self.curr.execute("""update gpus_tb set price = (?) where name = (?)""",
                          (item["price"], item["gpu_name"]))
        self.conn.commit()

    def process_item(self, item, spider):
        self.store_price_db(item)
        return item


if __name__ == '__main__':
    i = GpuImgScraperPipeline()
