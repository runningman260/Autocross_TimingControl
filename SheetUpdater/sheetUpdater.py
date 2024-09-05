#/bin/python3

##################################################################
#  Google sheet updater for views                                #
#  To be expanded with other leaderboards and possibly runtable  #
#  This script courtesy github copilot                           #
#  Client_script.json is the google api key - not committed      #
####################################### Pittsburgh Shootout LLC ##

import os, sys
from config import Config
from database_helper import *
import psycopg2
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import schedule
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Google Sheets configuration
SPREADSHEET_NAME = 'leaderrrrr'
LEADERBOARD_SHEET_NAME = 'testleaderboard'

# Function to fetch leaderboard data from the database
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
        cur.close()
        logging.info("Fetched leaderboard data from the database.")
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(f"Error fetching data from the database: {error}")
    finally:
        if conn is not None:
            conn.close()
    return leaderboard_data

# Function to update Google Sheets with leaderboard data
def update_google_sheet(data):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
        client = gspread.authorize(creds)
        sheet = client.open(SPREADSHEET_NAME).worksheet(LEADERBOARD_SHEET_NAME)
        
        # Clear existing data
        sheet.clear()
        
        # Update with new data
        
        sheet.append_rows(data)
        logging.info("Updated Google Sheet with new leaderboard data.")
    except Exception as e:
        logging.error(f"Error updating Google Sheet: {e}")

# Function to fetch data and update Google Sheets
def job():
    logging.info("Updating Google Sheets...")
    leaderboard_data = fetch_leaderboard()
    print(leaderboard_data)
    if leaderboard_data:
        update_google_sheet(leaderboard_data)
    logging.info("Google Sheets update complete.")

# Schedule the job to run every minute
schedule.every(1).minute.do(job)

# Keep the script running
logging.info("Sheet Updater started.")
while True:
    job()
    #schedule.run_pending()
    time.sleep(60)
