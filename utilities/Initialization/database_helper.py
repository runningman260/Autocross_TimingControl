#/bin/python3

#######################################################################################
#                                                                                     #
#  Common Helper Function to interact with a postgres database                        #
#                                                                                     #
############################################################ Pittsburgh Shootout LLC ##

from config import Config
import time
import psycopg2
import re

def run_query(command):
	response = None
	try:
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
			with conn.cursor() as cur:
				# execute the CREATE TABLE statement
				cur.execute(command)
				response = cur.fetchone()
	except (psycopg2.DatabaseError, Exception) as error:
		print(error)
	return response

def create_table(command):
    try:
        # Use regex to extract table name after CREATE TABLE (ignore whitespace/newlines)
        match = re.search(r'CREATE\s+TABLE\s+"?([a-zA-Z0-9_]+)"?', command, re.IGNORECASE)
        table_name = match.group(1) if match else 'unknown_table'
        print(f"[DB] Creating table: {table_name}")
        with psycopg2.connect(
            host=Config.DB.HOST, 
            database=Config.DB.NAME, 
            user=Config.DB.USER, 
            password=Config.DB.PASS) as conn:
            with conn.cursor() as cur:
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
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
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
		print(f"[DB] Dropping table: {table_name}")
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
			with conn.cursor() as cur:
				# execute the DROP TABLE statement
				cur.execute(sql)
	except (psycopg2.DatabaseError, Exception) as error:
		print(error)

def create_view(command):
    try:
        # Improved regex: handles quoted/unquoted, schema-qualified, multiline, and whitespace
        match = re.search(
            r'CREATE\s+VIEW\s+(?:[\w\."]+\.)?(?:"([^"]+)"|(\w+))',
            command, re.IGNORECASE | re.DOTALL
        )
        if match:
            view_name = match.group(1) or match.group(2)
            view_name = view_name.strip()
        else:
            # Fallback: find the first non-empty line after CREATE VIEW
            after_create_view = re.split(r'CREATE\s+VIEW', command, flags=re.IGNORECASE)[-1]
            lines = [l.strip() for l in after_create_view.splitlines() if l.strip()]
            view_name = lines[0][:40] + '...' if lines else 'unknown_view'
        print(f"[DB] Creating view: {view_name}")
        with psycopg2.connect(
            host=Config.DB.HOST, 
            database=Config.DB.NAME, 
            user=Config.DB.USER, 
            password=Config.DB.PASS) as conn:
            with conn.cursor() as cur:
                cur.execute(command)
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)

def delete_view(view_name):
	sql = "DROP VIEW IF EXISTS " + view_name + " CASCADE;"
	try:
		print(f"[DB] Dropping view: {view_name}")
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
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
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
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
	
def retrieve_oldest_active_run_by_scan_status(table_name, column_name):
	id = -1
	sql = """
		SELECT id FROM {table_name} 
		WHERE {column_name} is null 
		ORDER BY id LIMIT 1 
		;""".format(table_name=table_name, column_name=column_name)
	try:
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
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
	
def retrieve_oldest_active_run_by_raw_time(table_name, column_name):
	id = -1
	sql = """
		SELECT id FROM {table_name} 
		WHERE {column_name} is null 
		ORDER BY id LIMIT 1 
		;""".format(table_name=table_name, column_name=column_name)
	try:
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
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

def update_runtable(table_name, column_name, value, id):
	sql = """
		UPDATE {table_name} 
		SET {column_name} = '{value}'
		WHERE id = {id} 
		RETURNING id;
		""".format(table_name=table_name, column_name=column_name, value=value, id=id)
	
	return_id = None
	try:
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
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

def update_runtable_2col(table_name, column_1_name, value_1, column_2_name, value_2, id):
	sql = """
		UPDATE {table_name} 
		SET {column_1_name} = '{value_1}',
		{column_2_name} = '{value_2}'
		WHERE id = {id} 
		RETURNING id;
		""".format(table_name=table_name, column_1_name=column_1_name, value_1=value_1, column_2_name=column_2_name, value_2=value_2, id=id)
	
	return_id = None
	try:
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
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
	
def insert_rawlaptime(table_name, run_data):
	sql = """INSERT INTO {table_name}(read_counter, raw_time) VALUES({read_count}, '{raw_time}' ) RETURNING run_id;""".format(table_name=table_name, read_count=run_data[0], raw_time=run_data[1])

	run_id = None

	try:
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
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
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
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
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
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
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
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
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
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
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
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

def upsert_car(table_name, scan_time, tag_number, car_number, team_name, car_class):
	sql = """
		INSERT INTO carreg(scan_time, tag_number, car_number, team_name, class)
		values('{scan_time}','{tag_number}','{car_number}','{team_name}','{car_class}')
		ON CONFLICT(car_number)
		DO UPDATE SET
		tag_number = EXCLUDED.tag_number,
		scan_time = EXCLUDED.scan_time
		RETURNING (xmax = 0) AS _created;
		""".format(table_name=table_name, scan_time=scan_time, tag_number=tag_number, car_number=car_number, team_name=team_name, car_class=car_class)
	inserted_flag = -1

	try:
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
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
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
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
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
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
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
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
        print(f"[DB] Creating trigger: {trigger_name} on table: {table_name}")
        with psycopg2.connect(
            host=Config.DB.HOST, 
            database=Config.DB.NAME, 
            user=Config.DB.USER, 
            password=Config.DB.PASS) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)

def check_function_exists(function_name):
	exists = False
	command = """select exists(select * from pg_proc where proname = '{function_name}');""".format(function_name=function_name)
	try:
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
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
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
			with conn.cursor() as cur:
				# execute the CREATE TABLE statement
				cur.execute(command)
				exists = bool(cur.fetchone()[0])
	except (psycopg2.DatabaseError, Exception) as error:
		print(error)
	return exists

def delete_function(function_name):
	sql = "DROP FUNCTION IF EXISTS " + function_name + " CASCADE;"
	try:
		print(f"[DB] Dropping function: {function_name}")
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
			with conn.cursor() as cur:
				# execute the DROP TABLE statement
				cur.execute(sql)
	except (psycopg2.DatabaseError, Exception) as error:
		print(error)

def delete_trigger(trigger_name, table_name):
	sql = "DROP TRIGGER IF EXISTS " + trigger_name + " ON " + table_name + " CASCADE;"
	try:
		print(f"[DB] Dropping trigger: {trigger_name} on table: {table_name}")
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
			with conn.cursor() as cur:
				# execute the DROP TABLE statement
				cur.execute(sql)
	except (psycopg2.DatabaseError, Exception) as error:
		print(error)

def create_pg_notify_function(function_name):
	sql = """create or replace function {function_name}() 
	returns trigger as $$
	begin 
		perform pg_notify('new_id', row_to_json(new)::text);
		return new; 
	end; 
	$$ language plpgsql;""".format(function_name=function_name)
	try:
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
			with conn.cursor() as cur:
				# execute
				cur.execute(sql)
	except (psycopg2.DatabaseError, Exception) as error:
		print(error)


def create_pg_notify_trigger(table_name, function_name, trigger_name):
	sql = """
		CREATE OR REPLACE TRIGGER "{trigger_name}" 
		after insert or update on "{table_name}"
		FOR EACH ROW EXECUTE PROCEDURE {function_name}();""".format(function_name=function_name, trigger_name=trigger_name, table_name=table_name)
	try:
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
			with conn.cursor() as cur:
				# execute
				cur.execute(sql)
	except (psycopg2.DatabaseError, Exception) as error:
		print(error)

def create_autocross_runtable_update_adjusted_time_calc_function(table_name):
	sql = """CREATE OR REPLACE FUNCTION {table_name}_update_adjusted_time() 
		RETURNS TRIGGER AS $$
		BEGIN
			IF POSITION('DNF' IN UPPER(NEW.dnf)) > 0 THEN
				NEW.adjusted_time := 'DNF';
			ELSE
				NEW.adjusted_time := (COALESCE(CAST(NEW.raw_time AS NUMERIC),0) + (2 * CAST(NEW.cones AS NUMERIC)) + (10 * CAST(NEW.off_course AS NUMERIC)))::text;
			END IF;
			RETURN NEW;
		END;
		$$ LANGUAGE plpgsql;""".format(table_name=table_name)
	try:
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
			with conn.cursor() as cur:
				# execute
				cur.execute(sql)
	except (psycopg2.DatabaseError, Exception) as error:
		print(error)

def create_accel_runtable_update_adjusted_time_calc_function(table_name):
	sql = """CREATE OR REPLACE FUNCTION {table_name}_update_adjusted_time() 
		RETURNS TRIGGER AS $$
		BEGIN
			IF POSITION('DNF' IN UPPER(NEW.dnf)) > 0 OR POSITION('DNF' IN UPPER(NEW.raw_time)) > 0 OR (COALESCE(NULLIF(TRIM(NEW.off_course),''),'0') ~ '^[0-9]+$' AND CAST(NEW.off_course AS INTEGER) > 0) THEN
				NEW.adjusted_time := 'DNF';
			ELSE
				NEW.adjusted_time := (COALESCE(CAST(NEW.raw_time AS NUMERIC),0) + (2 * CAST(NEW.cones AS NUMERIC)))::text;
			END IF;
			RETURN NEW;
		END;
		$$ LANGUAGE plpgsql;""".format(table_name=table_name)
	try:
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
			with conn.cursor() as cur:
				# execute the function creation
				cur.execute(sql)
	except (psycopg2.DatabaseError, Exception) as error:
		print(error)

def create_skidpad_runtable_update_adjusted_time_calc_function(table_name):
	sql = """CREATE OR REPLACE FUNCTION {table_name}_update_adjusted_time() 
		RETURNS TRIGGER AS $$
		BEGIN
			IF POSITION('DNF' IN UPPER(NEW.dnf)) > 0 OR POSITION('DNF' IN UPPER(NEW.raw_time_left)) > 0 OR POSITION('DNF' IN UPPER(NEW.raw_time_right)) > 0 OR (COALESCE(NULLIF(TRIM(NEW.off_course),''),'0') ~ '^[0-9]+$' AND CAST(NEW.off_course AS INTEGER) > 0) THEN
				NEW.adjusted_time := 'DNF';
			ELSE
				NEW.adjusted_time := trunc((((COALESCE(CAST(NEW.raw_time_left AS NUMERIC),0) + COALESCE(CAST(NEW.raw_time_right AS NUMERIC),0)) / 2) + (CAST(0.125 AS NUMERIC) * CAST(NEW.cones AS NUMERIC))),3)::text;
			END IF;
			RETURN NEW;
		END;
		$$ LANGUAGE plpgsql;""".format(table_name=table_name)
	try:
		with psycopg2.connect(
			host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS) as conn:
			with conn.cursor() as cur:
				# execute the function creation
				cur.execute(sql)
	except (psycopg2.DatabaseError, Exception) as error:
		print(error)

def create_adjust_time_trigger(table_name):
    sql = """
        CREATE TRIGGER {table_name}_adjust_time_trigger
        BEFORE INSERT OR UPDATE ON "{table_name}"
        FOR EACH ROW
        EXECUTE FUNCTION {table_name}_update_adjusted_time();""".format(table_name=table_name)
    try:
        print(f"[DB] Creating trigger: {table_name}_adjust_time_trigger on table: {table_name}")
        with psycopg2.connect(
            host=Config.DB.HOST, 
            database=Config.DB.NAME, 
            user=Config.DB.USER, 
            password=Config.DB.PASS) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)


def insert_teams():
	teams = [
		("Clarkson University Clarkson FSAE", "CLARK"),
		("Wayne State University Warrior Racing", "WARR"),
		("Ecole de technologie superieure - Formule ETS", "ETS"),
		("MRacing Formula SAE", "MR"),
		("Univ of Connecticut Formula SAE", "UCONN"),
		("University of Waterloo Formula Electric", "UWFE"),
		("University of Ottawa", "FUO"),
		("University of Virginia Virginia Motorsports", "UVA"),
		("The Ohio State University - Formula Buckeyes", "OSU"),
		("North Carolina State University Pack Motorsports", "PACK"),
		("Oakland University Grizzlies Racing", "GRIZZ"),
		("Temple University Temple Formula Racing", "TMPL"),
		("Michigan Technological University Racing", "MTUR"),
		("Northern Illinois University Huskie Motorsports", "NIU"),
		("Villanova University NovaRacing", "NOVA"),
		("University of Cincinnati's Bearcats Racing", "CINCI"),
		("Michigan State University State Racing", "MSUR"),
		("University of Toledo Rocket Motorsports", "OTRM"),
		("Polytechnique Montreal Formule Polytechnique Montreal", "FPM"),
		("Pellissippi State Community College Motorsports", "PELL"),
		("Western University Western Formula Racing", "WFR"),
		("Penn State University Nittany Motorsports", "PSU"),
		("University of Windsor Lancer Motorsports", "UWLM"),
		("Rochester Institute of Technology RIT Racing", "RIT"),
		("University of Pittsburgh Panther Racing", "PITT"),
		("Western Michigan University Bronco Racing", "WMBR"),
		("The University of Akron Zips Racing", "AKRON"),
		("Rutgers Formula Racing", "RUT"),
		("Drexel University Formula SAE", "DREXL"),
		("Virginia Tech, VT Motorsports", "VTM"),
		("UIC Formula SAE", "UIC"),
		("York College of Pennsylvania YC Racing", "YCR"),
		("Liberty University Flames Racing", "LUFR"),
		("Carnegie Mellon Racing", "CMR"),
		("Kennesaw State University Kennesaw Motorsports", "KSUM"),
		("Superbaits University GC-Racing", "SUPER"),
		("West Virginia University Mountaineer Racing", "WVU"),
	]
	try:
		with psycopg2.connect(
			host=Config.DB.HOST,
			database=Config.DB.NAME,
			user=Config.DB.USER,
			password=Config.DB.PASS) as conn:
			with conn.cursor() as cur:
				for name, abbr in teams:
					cur.execute(
						"INSERT INTO team (name, abbreviation) VALUES (%s, %s) ON CONFLICT (abbreviation) DO NOTHING;",
						(name, abbr)
					)
				conn.commit()
	except (psycopg2.DatabaseError, Exception) as error:
		print(error)

def clear_and_create_schema():
	database_tables = {
		"team":
		"""
			CREATE TABLE team(
				id SERIAL PRIMARY KEY,
				name VARCHAR(255) NOT NULL,
				abbreviation VARCHAR(32) UNIQUE NOT NULL
			);""",
		"carreg":
		"""
			CREATE TABLE carreg(
				id SERIAL PRIMARY KEY,
				scan_time VARCHAR(255),
				tag_number  VARCHAR(255),
				car_number VARCHAR(255),
				team_id INTEGER REFERENCES team(id),
				class VARCHAR(255),
				year VARCHAR(4),
				created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
				updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
				UNIQUE (car_number)
			);""",
		"startlinescan":
		"""
			CREATE TABLE startlinescan(
				id SERIAL PRIMARY KEY,
				scan_number VARCHAR(255),
				tag_number  VARCHAR(255),
				created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
				updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
				created_by VARCHAR(255)
				);""",
		"finishlinescan":
		"""
			CREATE TABLE finishlinescan(
				id SERIAL PRIMARY KEY,
				scan_number VARCHAR(255),
				tag_number  VARCHAR(255),
				created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
				updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
				);""",
		"laptimeraw":
		"""
			CREATE TABLE laptimeraw(
				run_id SERIAL PRIMARY KEY,
				read_counter VARCHAR(255),
				raw_time  VARCHAR(255),
				created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
				updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
				);""",
		"runtable":
		"""
			CREATE TABLE runtable(
				id SERIAL PRIMARY KEY,
				car_number VARCHAR(255),
				startline_scan_status VARCHAR(255),
				finishline_scan_status VARCHAR(255),
				raw_time VARCHAR(255),
				cones VARCHAR(255) DEFAULT '0' NOT NULL,
				off_course VARCHAR(255) NOT NULL DEFAULT '0',
				dnf VARCHAR(255),
				adjusted_time VARCHAR(255),
				created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
				updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
				last_synced_at TIMESTAMPTZ
				);""",
		"accel_runtable":
		"""
			CREATE TABLE accel_runtable(
				id SERIAL PRIMARY KEY,
				car_number VARCHAR(255),
				raw_time VARCHAR(255),
				cones VARCHAR(255) DEFAULT '0' NOT NULL,
				off_course VARCHAR(255) NOT NULL DEFAULT '0',
				dnf VARCHAR(255),
				adjusted_time VARCHAR(255),
				created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
				updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
				last_synced_at TIMESTAMPTZ
				);""",
		"skidpad_runtable":
		"""
			CREATE TABLE skidpad_runtable(
				id SERIAL PRIMARY KEY,
				car_number VARCHAR(255),
				raw_time_left VARCHAR(255),
				raw_time_right VARCHAR(255),
				cones VARCHAR(255) DEFAULT '0' NOT NULL,
				off_course VARCHAR(255) NOT NULL DEFAULT '0',
				dnf VARCHAR(255),
				adjusted_time VARCHAR(255),
				created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
				updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
				last_synced_at TIMESTAMPTZ
				);"""
	}
	trigger_name = "_trigger_set_timestamp"
	function_name = "_set_timestamp"

	## Drop table and functions
	delete_table("carreg")
	delete_table("startlinescan")
	delete_table("finishlinescan")
	delete_table("runtable")
	delete_table("laptimeraw")
	delete_table("leaderboard")
	delete_table("team")
	delete_function("startlinescan_set_timestamp")
	delete_function("finishlinescan_set_timestamp")
	delete_function("runtable_set_timestamp")
	delete_function("laptimeraw_set_timestamp")
	delete_function("leaderboard_set_timestamp")
	delete_view("leaderboard")
	delete_table("points_leaderboard")
	delete_view("cones_leaderboard")

	delete_table("accel_runtable")
	delete_table("skidpad_runtable")

	for table_name in database_tables:
		delete_if_exists = False
		table_exists = False
		function_exists = False
		trigger_exists = False

		table_exists  = check_table_exist(table_name)
		function_name = table_name + "_set_timestamp"
		trigger_name  = table_name + "_trigger_set_timestamp"
		function_exists = check_function_exists(function_name) 
		trigger_exists  = check_trigger_exists(trigger_name)
		if(table_exists and delete_if_exists):
			#print("Deleting all rows from " + table_name + "...")
			delete_all_table_rows(table_name)
		if(not table_exists):
			create_table(database_tables[table_name])
		if(not function_exists):
			create_timestamp_function(function_name)
		if(not trigger_exists):
			create_timestamp_trigger(table_name, function_name, trigger_name)
		#print(table_name  + "\t\t\t Present: " + str(table_exists))
		#print(function_name + "\t\t Present: " + str(function_exists))
		#print(trigger_name  + "\t Present: " + str(trigger_exists))
		if(table_name == "runtable"):
			function_name = table_name + "_function_pg_nofity"
			trigger_name  = table_name + "_trigger_pg_nofity"
			# Notify that a new ID has been added
			create_pg_notify_function(function_name)
			# Trigger executes the function when the above nofify flag is raised
			create_pg_notify_trigger(table_name,function_name,trigger_name)
			# The Actual time adjustment function
			create_autocross_runtable_update_adjusted_time_calc_function(table_name)
			# Execute update_adjusted_time on insert or udate of the table
			create_adjust_time_trigger(table_name)
		if(table_name == "skidpad_runtable"):
			function_name = table_name + "_function_pg_nofity"
			trigger_name  = table_name + "_trigger_pg_nofity"
			create_pg_notify_function(function_name)
			create_pg_notify_trigger(table_name,function_name,trigger_name)
			create_skidpad_runtable_update_adjusted_time_calc_function(table_name)
			create_adjust_time_trigger(table_name)
		if(table_name == "accel_runtable"):
			function_name = table_name + "_function_pg_nofity"
			trigger_name  = table_name + "_trigger_pg_nofity"
			create_pg_notify_function(function_name)
			create_pg_notify_trigger(table_name,function_name,trigger_name)
			create_accel_runtable_update_adjusted_time_calc_function(table_name)
			create_adjust_time_trigger(table_name)
	insert_teams()



## 2025 Rules Reference with Pitt Shootout-specific modification
## 	(10 second OC penalty in AutoX rather than 20)
#
# Autocross Scoring
#	Scoring Term Definitions:
#		Corrected Time 		= Autocross Run Time + ( CONE * 2 ) + ( OC * 20 )
#		Tyour				= the best Corrected Time for the team
#		Tmin 				= the lowest Corrected Time recorded for any team
#		Tmax 				= 145% of Tmin
#		CONE Penalty		= 2 seconds
#		OFF COURSE Pentalty = 10 seconds
#	When Tyour < Tmax. the team score is calculated as:
#		Autocross Score = 118.5 x [( Tmax / Tyour ) -1] / [( Tmax / Tmin ) -1] + 6.5
#	When Tyour > Tmax:
# 		Autocross Score = 6.5
#
#
#
# Skidpad Scoring
#	Scoring Term Definitions:
# 		Corrected Time 		= ( Right Lap Time + Left Lap Time ) / 2 + ( CONE * 0.125 )
#		Tyour 				= the best Corrected Time for the team
#		Tmin 				= is the lowest Corrected Time recorded for any team
#		Tmax 				= 125% of Tmin
#		CONE Penalty		= 0.125 seconds
#		OFF COURSE Pentalty = DNF
#	When Tyour < Tmax. the team score is calculated as:
#		Skidpad Score = 71.5 x [( Tmax / Tyour )^2 -1] / [( Tmax / Tmin )^2 -1] + 3.5
#	When Tyour > Tmax:
# 		Skidpad Score = 3.5
#
#
#
# Acceleration 
#	Scoring Term Definitions:
#		Corrected Time 		= Acceleration Run Time + ( CONE * 2 )
#		Tyour 				= the best Corrected Time for the team
#		Tmin 				= the lowest Corrected Time recorded for any team
#		Tmax 				= 150% of Tmin
#		CONE Penalty		= 2 seconds
#		OFF COURSE Pentalty = DNF
#	When Tyour < Tmax. the team score is calculated as:
#		Acceleration Score = 95.5 x [( Tmax / Tyour ) -1] / [( Tmax / Tmin ) -1] + 4.5
#	When Tyour > Tmax:
#		Acceleration Score = 4.5
