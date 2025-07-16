import requests
import csv
from datetime import datetime
import os
import time

#URL_HOST = 'http://localhost:5000/'
URL_HOST = os.getenv('TRACKAPI_HOST')
API_URL = URL_HOST + 'api/update_car_regs'
TEAMS_URL = URL_HOST + 'api/teams'
AUTH = os.getenv('TRACKAPI_AUTH_TOKEN')

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

    # Hardcoded values for Montreal 2024, class 'PGE'
    car_number = "F99"
    team_name = "Polytechnique Montreal Formule Polytechnique Montreal"
    class_ = "PGE"  # Override to 'PGE'
    year = "2024"

    # Normalize team name for matching
    norm_team_name = team_name.lower()
    team = team_lookup.get(norm_team_name)
    if not team:
        print(f"WARNING: Team not found for '{team_name}'. Skipping car_number {car_number}.")
        return

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

if __name__ == "__main__":
    main()
