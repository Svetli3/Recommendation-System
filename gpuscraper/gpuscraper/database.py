import sqlite3

conn = sqlite3.connect("gpus.db")
curr = conn.cursor()

curr.execute("""create table gpus_tb(
                brand text,
                name text,
                clock_speed integer,
                memory_size integer,
                memory_speed integer,
                memory_type integer,
                bus_width integer
                )""")