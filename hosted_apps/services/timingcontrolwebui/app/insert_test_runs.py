import sys
import os
import random
from datetime import datetime

# Ensure app import works from project root or app dir
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import RunOrder, CarReg

app = create_app()

def insert_test_runs(n=20):
    with app.app_context():
        # Fetch all real car numbers from CarReg
        car_numbers = [car.car_number for car in db.session.query(CarReg).all()]
        if not car_numbers:
            print("No car numbers found in CarReg. Aborting test run insertion.")
            return

        for i in range(n):
            car_number = random.choice(car_numbers)
            run = RunOrder(
                car_number=car_number,
                raw_time=round(random.uniform(50, 80), 3),
                adjusted_time=round(random.uniform(50, 80), 3),
                cones=random.randint(0, 3),
                off_course=random.randint(0, 1),
                dnf='DNF' if random.random() < 0.1 else '',
                startline_scan_status='Test Insert'
            )
            db.session.add(run)
        db.session.commit()
        print(f"Inserted {n} test runs using real car numbers from CarReg.")

if __name__ == "__main__":
    insert_test_runs(20)  # Change 20 to however many you want