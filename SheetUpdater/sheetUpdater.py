#/bin/python3

##################################################################
#  Google sheet updater for views                                #
#  To be expanded with other leaderboards and possibly runtable  #
#  This script courtesy github copilot                           #
#  client_secret.json is the google api key - not committed      #
####################################### Pittsburgh Shootout LLC ##


from decimal import Decimal
import os, sys
from config import Config
from database_helper import *
import psycopg2
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import schedule
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Google Sheets configuration
SPREADSHEET_NAME = '2024 Pittsburgh Shootout Automated Live Timing'
LEADERBOARD_SHEET_NAME = 'leaderboard'
RUNTABLE_SHEET_NAME = 'runtable'
CONE_SHEET_NAME = 'coneLeaderboard'
IC_POINTS_SHEET_NAME = 'pointsLeaderboardIC'
EV_POINTS_SHEET_NAME = 'pointsLeaderboardEV'

# Function to fetch leaderboard data from the database
def fetch_runtable():
    conn = None
    rows = []
    try:
        conn = psycopg2.connect(
           host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS
        )
        cur = conn.cursor()
        cur.execute("SELECT id, car_number, raw_time, cones, off_course, adjusted_time FROM runtable order by id")  # Adjust the query as needed
        rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]
        
        # Convert datetime columns to strings
        
        # for row in rows:
        #     row_dict = dict(zip(col_names, row))
        #     for col_name, value in row_dict.items():
        #         if isinstance(value, datetime):
        #             row_dict[col_name] = value.strftime('%Y-%m-%d %H:%M:%S')
        #     leaderboard_data.append(list(row_dict.values()))
        rows.insert(0, col_names)
        cur.close()
        logging.info("Fetched runtable data from the database.")
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(f"Error runtable data from the database: {error}")
    finally:
        if conn is not None:
            conn.close()
    return rows

def fetch_leaderboard():
    conn = None
    leaderboard_data = []
    try:
        conn = psycopg2.connect(
           host=Config.DB.HOST, 
			database=Config.DB.NAME, 
			user=Config.DB.USER, 
			password=Config.DB.PASS
        )
        cur = conn.cursor()
        cur.execute("SELECT * FROM leaderboard")  # Adjust the query as needed
        leaderboard_data = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]
        
        leaderboard_data.insert(0, col_names)
        cur.close()
        logging.info("Fetched leaderboard data from the database.")
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(f"Error fetching data from the database: {error}")
    finally:
        if conn is not None:
            conn.close()
    return leaderboard_data

def fetch_cone_leaderboard():
    conn = None
    leaderboard_data = []
    try:
        conn = psycopg2.connect(
           host=Config.DB.HOST, 
            database=Config.DB.NAME, 
            user=Config.DB.USER, 
            password=Config.DB.PASS
        )
        cur = conn.cursor()
        cur.execute("SELECT * FROM cones_leaderboard")  # Adjust the query as needed
        leaderboard_data = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]
        
        leaderboard_data.insert(0, col_names)
        cur.close()
        logging.info("Fetched cone leaderboard data from the database.")
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(f"Error fetching data from the database: {error}")
    finally:
        if conn is not None:
            conn.close()
    return leaderboard_data

def fetch_EV_points_leaderboard():
    conn = None
    leaderboard_data = []
    try:
        conn = psycopg2.connect(
           host=Config.DB.HOST, 
            database=Config.DB.NAME, 
            user=Config.DB.USER, 
            password=Config.DB.PASS
        )
        cur = conn.cursor()
        cur.execute("SELECT * FROM points_leaderboard_ev")  # Adjust the query as needed
        leaderboard_data = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]
        leaderboard_data = [
            [float(item) if isinstance(item, Decimal) else item for item in row]
            for row in leaderboard_data]
                
        leaderboard_data.insert(0, col_names)
        cur.close()
        logging.info("Fetched EV points leaderboard data from the database.")
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(f"Error fetching data from the database: {error}")
    finally:
        if conn is not None:
            conn.close()
    return leaderboard_data

def fetch_IC_points_leaderboard():
    conn = None
    leaderboard_data = []
    try:
        conn = psycopg2.connect(
           host=Config.DB.HOST, 
            database=Config.DB.NAME, 
            user=Config.DB.USER, 
            password=Config.DB.PASS
        )
        cur = conn.cursor()
        cur.execute("SELECT * FROM points_leaderboard_ic")  # Adjust the query as needed
        leaderboard_data = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]
        leaderboard_data = [
            [float(item) if isinstance(item, Decimal) else item for item in row]
            for row in leaderboard_data]
                
        leaderboard_data.insert(0, col_names)
        cur.close()
        logging.info("Fetched IC points leaderboard data from the database.")
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(f"Error fetching data from the database: {error}")
    finally:
        if conn is not None:
            conn.close()
    return leaderboard_data

# Function to update Google Sheets with leaderboard data
def update_google_sheet(data, sheet_name):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
        client = gspread.authorize(creds)
        sheet = client.open(SPREADSHEET_NAME).worksheet(sheet_name)
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data[0].append(current_timestamp)
        # Clear existing data
        #sheet.clear()
        # Update with new data
        #sheet.append_rows(data)
        sheet.update(data, 'A1')
        logging.info("Updated Google Sheet")
    except Exception as e:
        logging.error(f"Error updating Google Sheet: {e}")

# Function to fetch data and update Google Sheets
def jobLeaderboard():
    
    leaderboard_data = fetch_leaderboard()
    #print(leaderboard_data)
    logging.info("Updating Leaderboard..")
    if leaderboard_data:
        update_google_sheet(leaderboard_data, LEADERBOARD_SHEET_NAME)
    logging.info("Leaderboard update complete.")

def jobruntable():
    runtable_data = fetch_runtable()
    #print(runtable_data)
    logging.info("Updating Runtable...")
    if runtable_data:
        update_google_sheet(runtable_data, RUNTABLE_SHEET_NAME)
    logging.info("Runtable update complete.")

def jobconeLeaderboard():
    cone_leaderboard_data = fetch_cone_leaderboard()
    #print(cone_leaderboard_data)
    logging.info("Updating Cone Leaderboard...")
    if cone_leaderboard_data:
        update_google_sheet(cone_leaderboard_data, CONE_SHEET_NAME)
    logging.info("Cone Leaderboard update complete.")

def jobEVpointsLeaderboard():
    points_leaderboard_data = fetch_EV_points_leaderboard()
    #print(points_leaderboard_data)
    logging.info("Updating EV Points Leaderboard...")
    if points_leaderboard_data:
        update_google_sheet(points_leaderboard_data, EV_POINTS_SHEET_NAME)
    logging.info("EV Points Leaderboard update complete.")

def jobICpointsLeaderboard():
    points_leaderboard_data = fetch_IC_points_leaderboard()
    #print(points_leaderboard_data)
    logging.info("Updating IC Points Leaderboard...")
    if points_leaderboard_data:
        update_google_sheet(points_leaderboard_data, IC_POINTS_SHEET_NAME)
    logging.info("IC Points Leaderboard update complete.")

schedule.every(15).seconds.do(jobLeaderboard)
time.sleep(3)
schedule.every(15).seconds.do(jobruntable)
time.sleep(3)  
schedule.every(15).seconds.do(jobconeLeaderboard)
time.sleep(3)
schedule.every(15).seconds.do(jobEVpointsLeaderboard)
time.sleep(3)
schedule.every(15).seconds.do(jobICpointsLeaderboard)

# Keep the script running
logging.info("Sheet Updater started.")
while True:
    # jobLeaderboard()
    # jobruntable()
    # jobconeLeaderboard()
    # jobpointsLeaderboard()
    schedule.run_pending()
    time.sleep(1)
    
