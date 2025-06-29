import requests
import csv
from datetime import datetime
import os
import time

#URL_HOST = 'http://localhost:5000/'
URL_HOST = 'https://trackapi.guttenp.land/'  # Use this for production
API_URL = URL_HOST + 'api/update_car_regs'
TEAMS_URL = URL_HOST + 'api/teams'
AUTH = 'P59d46bV5Xy40TblyzZR6J4dz4TlJ12lIswu2iiDYw2Hr8RqtPHoAWyWC8aevdDwVLJUsurbOo4M2aSSOFmmJ5DgaItek34yHYGTAyosU7GIBYhKBuihv3GyDPlCcr6fiKk7J3w0JE1yQeqbP2UPhjfyq63Azjd1wKK8Uhl3CUqJ4BPjipvzA1W1rQXFW1xc9Qdjqcs9IwrQ3edfPXSivYL'

def get_teams():
    headers = {"Authorization": AUTH}
    resp = requests.get(TEAMS_URL, headers=headers)
    resp.raise_for_status()
    teams = resp.json()
    # Build a lookup dict: normalized name -> team dict
    team_lookup = {}
    for team in teams:
        norm_name = team['name'].strip().lower()
        team_lookup[norm_name] = team
    return team_lookup

def main():
    # Fetch teams from API
    try:
        team_lookup = get_teams()
    except Exception as e:
        print(f"Failed to fetch teams: {e}")
        return

    # Read data from the CSV file
    csv_file_path = os.path.join(os.path.dirname(__file__), "2025_reg.csv")
    if not os.path.exists(csv_file_path):
        print(f"CSV file not found at {csv_file_path}")
        exit(1)

    try:
        with open(csv_file_path, mode="r", newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                car_number = row[0].strip()
                team_name = row[1].strip()
                class_ = row[2].strip()
                year = row[3].strip() if len(row) > 3 else ""

                # Normalize team name for matching
                norm_team_name = team_name.lower()
                team = team_lookup.get(norm_team_name)
                if not team:
                    print(f"WARNING: Team not found for '{team_name}'. Skipping car_number {car_number}.")
                    continue

                car_reg = {
                    "scan_time": datetime.now().isoformat(),
                    "tag_number": car_number,
                    "car_number": car_number,
                    "team_id": team['id'],
                    "class_": class_,
                    "year": year
                }
                payload = {"car_regs": [car_reg]}
                print("Payload:", payload)
                headers = {"Authorization": AUTH}
                try:
                    response = requests.post(API_URL, json=payload, headers=headers)
                    print("Status Code:", response.status_code)
                    try:
                        print("Response JSON:", response.json())
                    except Exception as e:
                        print(f"Error decoding JSON response: {e}")
                except Exception as e:
                    print(f"Request failed: {e}")
                time.sleep(1)  # Delay 1 second between requests
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
