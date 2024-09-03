import psycopg2
from config import load_config
import csv
import time

def create_table():
    """ Create table in the PostgreSQL database"""
    command = (
        """
        CREATE TABLE run_order(
            run_id SERIAL PRIMARY KEY,
            team_name VARCHAR(255),
            location VARCHAR(255),
            tag VARCHAR(255),
            car_number VARCHAR(255),
            cones VARCHAR(255),
            off_course VARCHAR(255),
            raw_time  VARCHAR(255),
            adjusted_time VARCHAR(255)
        )
        """)
    try:
        config = load_config()
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                # execute the CREATE TABLE statement
                cur.execute(command)
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)

def insert_run(run_data):
    """ Insert a new run into the run_order table """

    sql = """INSERT INTO run_order(team_name, location, tag, car_number, cones, off_course, raw_time, adjusted_time)
             VALUES(%s, %s, %s, %s, %s, %s, %s, %s) RETURNING run_id;"""

    run_id = None
    config = load_config()

    try:
        with  psycopg2.connect(**config) as conn:
            with  conn.cursor() as cur:
                # execute the INSERT statement
                cur.execute(sql, (run_data))

                # get the generated id back
                rows = cur.fetchone()
                if rows:
                    run_id = rows[0]

                # commit the changes to the database
                conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        return run_id

def delete_table(table_name):
    sql = """DROP TABLE IF EXISTS %s CASCADE;"""
    try:
        config = load_config()
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                # execute the DROP TABLE statement
                cur.execute(sql, (table_name))
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)

def delete_all_table_rows(table_name):
    sql = """TRUNCATE %s;"""
    try:
        config = load_config()
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                # execute the DROP TABLE statement
                cur.execute(sql, (table_name))
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)

def remove_listener(channel_name):
    sql = """UNLISTEN %s;"""
    try:
        config = load_config()
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (channel_name))
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)

def create_listener(channel_name):
    sql = """LISTEN %s;"""
    try:
        config = load_config()
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (channel_name))
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)

def remove_function(function_name):
    sql = """DROP %s CASCADE;"""
    try:
        config = load_config()
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (function_name))
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)

def remove_trigger(trigger_name):
    sql = """DROP %s CASCADE;"""
    try:
        config = load_config()
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (trigger_name))
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)



if __name__ == '__main__':
    table_name = "run_order"
    delete_all_table_rows(table_name)
    
    with open('team_entry_data.csv') as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        next(readCSV, None)  # skip the headers
        for row in readCSV:
            print("Inserting: " + str(row))
            insert_run(row)
            time.sleep(2)
