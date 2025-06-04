#!/bin/python3

# Listen for the triggered notification from the database
# Print the payload, which in this case should be the
#   entire new row sent as a JSON.


import psycopg2
from config import load_config
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import select

def dblistener():
    try:
        config = load_config()
        with psycopg2.connect(**config) as conn:
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            cur.execute("LISTEN new_id;")
            conn.commit()
            while True:
                #select.select([conn], [], [])
                #if select.select([conn],[],[],5) == ([],[],[]):
                #    print("Timeout")
                #else:
                    conn.poll()
                    while conn.notifies:
                        notify = conn.notifies.pop(0)
                        print("Got NOTIFY:", notify.pid, notify.channel, notify.payload)
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)


if __name__ == '__main__':
    dblistener()


