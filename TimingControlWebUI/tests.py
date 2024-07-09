#!/usr/bin/env python
from datetime import datetime, timezone, timedelta
import unittest
from app import create_app, db
from app.models import RunOrder
from config import Config
import csv
import time


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    ELASTICSEARCH_URL = None


class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_periodically_add_runs(self):
        time_between_runs = 30 # seconods
        with open('team_entry_data.csv') as csvfile:
            readCSV = csv.reader(csvfile, delimiter=',')
            next(readCSV, None)  # skip the headers
            for row in readCSV:
                print("Inserting: " + str(row))
                r = RunOrder(team_name=row[0], location=row[1], tag=row[2], car_number=row[3], cones=row[4], off_courses=row[5], raw_time=row[6], adjusted_time=row[7])
                db.session.add(r)
                db.session.commit()
                print(RunOrder.query.order_by(RunOrder.id.desc()).first().print_row())
                time.sleep(time_between_runs)

if __name__ == '__main__':
    unittest.main(verbosity=2)
