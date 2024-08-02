#!/usr/bin/env python
from datetime import datetime, timezone, timedelta
import unittest
from app import create_app, db
from app.models import CarReg
from config import Config
import csv
import time
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class TestConfig(Config):
    TESTING = True
    #SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_DATABASE_URI = 'postgresql://nick:password@localhost/test_scans'
    ELASTICSEARCH_URL = None

def float_input(s):
    
    try:
        x = float(s)
        return x
    except ValueError:
        return 0



class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        #db.drop_all()
        self.app_context.pop()



    def test_periodically_add_runs(self):
        # time_between_runs = 30 # seconods
        with open('car_reg_data.csv') as csvfile:
            readCSV = csv.reader(csvfile, delimiter=',')
            next(readCSV, None)  # skip the headers
            for row in readCSV:
                print("Inserting: " + str(row))
                r = CarReg(tag=row[1], car_number=row[2], team_name=row[0], scan_time = datetime.now())
                db.session.add(r)
                db.session.commit()
                #print(CarReg.query.order_by(CarReg.id.desc()).first().print_row())
                #time.sleep(time_between_runs)

if __name__ == '__main__':
    unittest.main(verbosity=2)

