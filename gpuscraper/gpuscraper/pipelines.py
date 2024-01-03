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
        self.conn = sqlite3.connect("gpus.db")
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