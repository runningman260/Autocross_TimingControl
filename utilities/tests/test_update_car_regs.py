import requests
import csv
from datetime import datetime
import os
import time

# Define the API endpoint
API_URL = "https://trackapi.guttenp.land/api/update_car_regs"
AUTH = 'P59d46bV5Xy40TblyzZR6J4dz4TlJ12lIswu2iiDYw2Hr8RqtPHoAWyWC8aevdDwVLJUsurbOo4M2aSSOFmmJ5DgaItek34yHYGTAyosU7GIBYhKBuihv3GyDPlCcr6fiKk7J3w0JE1yQeqbP2UPhjfyq63Azjd1wKK8Uhl3CUqJ4BPjipvzA1W1rQXFW1xc9Qdjqcs9IwrQ3edfPXSivYL'

def main():
    # Read data from the CSV file
    csv_file_path = os.path.join(os.path.dirname(__file__), "2025_reg.csv")
    if not os.path.exists(csv_file_path):
        print(f"CSV file not found at {csv_file_path}")
        exit(1)

    try:
        with open(csv_file_path, mode="r") as file:
            reader = csv.reader(file)
            for row in reader:
                car_reg = {
                    "scan_time": datetime.now().isoformat(),
                    "tag_number": row[0],
                    "car_number": row[0],
                    "team_name": row[1],
                    "class_": row[2]
                }
                payload = {"car_regs": [car_reg]}
                print("Payload:", payload)
                headers = {"Authorization": f"{AUTH}"}
                response = requests.post(API_URL, json=payload, headers=headers)
                print("Status Code:", response.status_code)
                print("Response JSON:", response.json())
                time.sleep(3)  # Delay 1 second between requests
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
