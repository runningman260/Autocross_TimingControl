#/bin/python3

#######################################################################################
#                                                                                     #
#  Helper Function to interact with a postgres database                               #
#                                                                                     #
############################################################ Pittsburgh Shootout LLC ##

from config import Config
import time
import psycopg2

def create_table(command):
    try:
        with psycopg2.connect(**Config.DATABASE) as conn:
            with conn.cursor() as cur:
                # execute the CREATE TABLE statement
                cur.execute(command)
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)

def check_table_exist(table_name):
    exists = False
    command = """
		SELECT EXISTS (
			SELECT FROM information_schema.tables 
			WHERE table_schema = current_schema() 
			AND table_name = '{table_name}'
			);""".format(table_name=table_name)
    try:
        with psycopg2.connect(**Config.DATABASE) as conn:
            with conn.cursor() as cur:
                # execute the CREATE TABLE statement
                cur.execute(command)
                exists = bool(cur.fetchone()[0])
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)
    return exists

def delete_table(table_name):
    sql = "DROP TABLE IF EXISTS " + table_name + " CASCADE;"
    try:
        with psycopg2.connect(**Config.DATABASE) as conn:
            with conn.cursor() as cur:
                # execute the DROP TABLE statement
                cur.execute(sql)
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)

def insert_rawlaptime(table_name, run_data):
    sql = """INSERT INTO {table_name}(read_counter, raw_time) VALUES({read_count}, '{raw_time}' ) RETURNING run_id;""".format(table_name=table_name, read_count=run_data[0], raw_time=run_data[1])

    run_id = None

    try:
        with  psycopg2.connect(**Config.DATABASE) as conn:
            with  conn.cursor() as cur:
                # execute the INSERT statement
                cur.execute(sql)

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

def update_rawlaptime(table_name, run_data, id = None):
    # IF id is provided, update will occur on record with run_id=id. 
    # IF id is NOT provided, update will occur on record with read_counter=run_data[0]
    # Single quotes around read_counter can be removed if field is declared as an int later
    if(id == None):
        sql = """UPDATE {table_name} SET raw_time = '{time}' WHERE read_counter = '{read_counter}' RETURNING run_id;""".format(table_name=table_name, read_counter=run_data[0], time=run_data[1])
    else:
        sql = """UPDATE {table_name} SET raw_time = '{time}' WHERE run_id = {id} RETURNING run_id;""".format(table_name=table_name, id=id, time=run_data[1])

    run_id = None
    try:
        with  psycopg2.connect(**Config.DATABASE) as conn:
            with  conn.cursor() as cur:
                # execute the INSERT statement
                cur.execute(sql)

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
    
def delete_all_table_rows(table_name):
    sql = "TRUNCATE " + table_name + ";"
    try:
        with psycopg2.connect(**Config.DATABASE) as conn:
            with conn.cursor() as cur:
                # execute
                cur.execute(sql)
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)

def create_timestamp_function(function_name):
    sql = """create or replace function {function_name}() 
    returns trigger as $$
    begin 
        NEW.updated_at = NOW();
        return new; 
    end; 
    $$ language plpgsql;""".format(function_name=function_name)
    try:
        with psycopg2.connect(**Config.DATABASE) as conn:
            with conn.cursor() as cur:
                # execute
                cur.execute(sql)
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)
          
def create_timestamp_trigger(table_name, function_name, trigger_name):
    sql = "CREATE TRIGGER {trigger_name} BEFORE UPDATE ON " + table_name + " FOR EACH ROW EXECUTE PROCEDURE {function_name}();".format(function_name=function_name, trigger_name=trigger_name)
    try:
        with psycopg2.connect(**Config.DATABASE) as conn:
            with conn.cursor() as cur:
                # execute
                cur.execute(sql)
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)

def check_function_exists(function_name):
    exists = False
    command = """select exists(select * from pg_proc where proname = '{function_name}');""".format(function_name=function_name)
    try:
        with psycopg2.connect(**Config.DATABASE) as conn:
            with conn.cursor() as cur:
                # execute the CREATE TABLE statement
                cur.execute(command)
                exists = bool(cur.fetchone()[0])
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)
    return exists

def check_trigger_exists(trigger_name):
    exists = False
    command = """select exists (select trigger_name FROM information_schema.triggers where trigger_name = '{trigger_name}');""".format(trigger_name=trigger_name)
    try:
        with psycopg2.connect(**Config.DATABASE) as conn:
            with conn.cursor() as cur:
                # execute the CREATE TABLE statement
                cur.execute(command)
                exists = bool(cur.fetchone()[0])
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)
    return exists