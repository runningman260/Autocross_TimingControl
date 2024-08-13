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

def create_new_run(table_name,car_number,startline_scan_status):
    run_created = None
    sql = """
        INSERT INTO {table_name}(car_number,startline_scan_status) 
        VALUES('{car_number}', '{startline_scan_status}') 
        RETURNING id;""".format(table_name=table_name,car_number=car_number,startline_scan_status=startline_scan_status)
    try:
        with  psycopg2.connect(**Config.DATABASE) as conn:
            with  conn.cursor() as cur:
                # execute the INSERT statement
                cur.execute(sql)

                # get the generated id back
                rows = cur.fetchone()
                if rows:
                    id = rows[0]

                # commit the changes to the database
                conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if(id is not None): run_created = id
        return run_created

def insert_newscan(table_name, tag_number, scan_number=None, created_by=None):
    if(created_by == None):
        sql = """
            INSERT INTO {table_name}(tag_number, scan_number) 
            VALUES('{tag_number}', '{scan_number}') 
            RETURNING id;""".format(table_name=table_name, tag_number=tag_number, scan_number=scan_number)
    else:
        sql = """
            INSERT INTO {table_name}(tag_number, created_by, scan_number) 
            VALUES('{tag_number}', '{created_by}', '{scan_number}') 
            RETURNING id;""".format(table_name=table_name, tag_number=tag_number, scan_number=scan_number, created_by=created_by)
    id = None
    try:
        with  psycopg2.connect(**Config.DATABASE) as conn:
            with  conn.cursor() as cur:
                # execute the INSERT statement
                cur.execute(sql)

                # get the generated id back
                rows = cur.fetchone()
                if rows:
                    id = rows[0]

                # commit the changes to the database
                conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        return id

def insert_newcar(table_name, scan_time, tag_number, car_number, team_name):
    sql = """
        INSERT INTO {table_name}(scan_time, tag_number, car_number, team_name) 
        VALUES('{scan_time}', '{tag_number}', '{car_number}', '{team_name}') 
        RETURNING id;""".format(table_name=table_name, scan_time=scan_time, tag_number=tag_number, car_number=car_number, team_name=team_name)

    id = None

    try:
        with  psycopg2.connect(**Config.DATABASE) as conn:
            with  conn.cursor() as cur:
                # execute the INSERT statement
                cur.execute(sql)

                # get the generated id back
                rows = cur.fetchone()
                if rows:
                    id = rows[0]

                # commit the changes to the database
                conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        return id

def update_newcar(table_name, scan_time, tag_number, car_number=None, team_name=None, id=None):
    if(id != None):
        sql = """
            UPDATE {table_name} 
            SET tag_number = '{tag_number}', scan_time = '{scan_time}' 
            WHERE id = {id} 
            RETURNING id;
            """.format(table_name=table_name, scan_time=scan_time, tag_number=tag_number, id=id)

    elif(car_number != None):
        sql = """        
            UPDATE {table_name} 
            SET tag_number = '{tag_number}', scan_time = '{scan_time}' 
            WHERE car_number = '{car_number}'
            RETURNING id;
            """.format(table_name=table_name, scan_time=scan_time, tag_number=tag_number, car_number=car_number)
    elif(team_name != None):
        sql = """
            UPDATE {table_name} 
            SET tag_number = '{tag_number}', scan_time = '{scan_time}' 
            WHERE team_name = '{team_name}'
            RETURNING id;
            """.format(table_name=table_name, scan_time=scan_time, tag_number=tag_number, team_name=team_name)
    else:
        return -1

    return_id = None
    try:
        with  psycopg2.connect(**Config.DATABASE) as conn:
            with  conn.cursor() as cur:
                # execute the INSERT statement
                cur.execute(sql)

                # get the generated id back
                rows = cur.fetchone()
                if rows:
                    return_id = rows[0]

                # commit the changes to the database
                conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        return return_id

def merge_car(table_name, scan_time, tag_number, car_number, team_name):
    sql = """
        MERGE INTO carreg w
        USING (values('{scan_time}','{tag_number}','{car_number}','{team_name}')) as v
        ON v.column3 = w.car_number
        WHEN NOT MATCHED THEN
        INSERT (scan_time, tag_number, car_number, team_name)
        values(v.column1,v.column2,v.column3,v.column4)
        WHEN MATCHED THEN
        UPDATE SET tag_number = v.column2;
        """.format(table_name=table_name, scan_time=scan_time, tag_number=tag_number, car_number=car_number, team_name=team_name)
    id = None

    try:
        with  psycopg2.connect(**Config.DATABASE) as conn:
            with  conn.cursor() as cur:
                # execute the INSERT statement
                cur.execute(sql)

                # get the generated id back
                rows = cur.fetchone()
                if rows:
                    id = rows[0]

                # commit the changes to the database
                conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        return id

def upsert_car(table_name, scan_time, tag_number, car_number, team_name):
    sql = """
        INSERT INTO carreg(scan_time, tag_number, car_number, team_name)
        values('{scan_time}','{tag_number}','{car_number}','{team_name}')
        ON CONFLICT(car_number)
        DO UPDATE SET
        tag_number = EXCLUDED.tag_number,
        scan_time = EXCLUDED.scan_time
        RETURNING (xmax = 0) AS inserted;
        """.format(table_name=table_name, scan_time=scan_time, tag_number=tag_number, car_number=car_number, team_name=team_name)
    inserted_flag = None

    try:
        with  psycopg2.connect(**Config.DATABASE) as conn:
            with  conn.cursor() as cur:
                # execute the INSERT statement
                cur.execute(sql)

                # get the generated inserted_flag back
                rows = cur.fetchone()
                if rows:
                    inserted_flag = rows[0]

                # commit the changes to the database
                conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        return inserted_flag
    
def get_car_number(table_name, tag_number):
    car_number = -1
    response = None
    sql = """
        SELECT car_number from {table_name} where tag_number = '{tag_number}';
        """.format(table_name=table_name, tag_number=tag_number)
    try:
        with psycopg2.connect(**Config.DATABASE) as conn:
            with conn.cursor() as cur:
                # execute the CREATE TABLE statement
                cur.execute(sql)
                response = cur.fetchone()[0]
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)
    if response is not None: car_number = response
    return car_number
    
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
    sql = """
        CREATE TRIGGER "{trigger_name}" 
        BEFORE UPDATE ON "{table_name}"
        FOR EACH ROW EXECUTE PROCEDURE {function_name}();""".format(function_name=function_name, trigger_name=trigger_name, table_name=table_name)
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