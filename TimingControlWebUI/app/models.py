from datetime import datetime, timezone, timedelta
from hashlib import md5
import json
import secrets
from time import time
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import current_app, url_for
from app import db
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
# Eventually this database should have the following columns
# Not all of them will be displayed on the site

# id: unique indentifier, primary key
# team_name: varchar128
# tag: varchar128
# car_number: int
# startline_scan_timestamp: varchar128
# finishline_scan_timestamp: varchar128

#CarReg Database
#id
#tag
#car_number
#team_name

# Leaderboard Database
#  place
#  run_number
#  car_number
#  team_name
#  raw_time
#  adjusted_time



class RunOrder(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    team_name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    location: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    tag: so.Mapped[str] = so.mapped_column(sa.String(128), index=True, primary_key=True)
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    cones: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True) 
    off_courses: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True)
    dnfs: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True)
    raw_time: so.Mapped[float] = so.mapped_column(sa.Numeric(5,2), index=True)
    adjusted_time: so.Mapped[float] = so.mapped_column(sa.Numeric(5,2), index=True)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False, default=datetime.now) 
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False, default=datetime.now) 
    
    
    def __repr__(self):
        return '<RunOrder {}>'.format(self.id)
    
    # This is dumb, need to find a better way
    def print_row(self):
        return '{}; {}; {}; {}; {}; {}; {}; {}; {}; {};'.format(self.id, self.team_name, self.location, self.tag, self.car_number, self.cones, self.off_courses, self.dnfs, self.raw_time, self.adjusted_time)

class CarReg(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    scan_time: so.Mapped[datetime] = so.mapped_column(sa.DateTime)
    tag: so.Mapped[str] = so.mapped_column(sa.String(128), index=True, unique=True)
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    team_name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False, default=datetime.now)
    

class TopLaps(db.Model):
    __tablename__ = 'top_runs'
    __table_args__ = {'info': {'is_view': True}}
    
    # Assuming 'id' is a column in your view. You need to define at least one column manually,
    # typically the primary key or a column you'll frequently query against.
    #id = db.Column(db.Integer, primary_key=True)
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    team_name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    location: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    tag: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    cones: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True) 
    off_courses: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True)
    dnfs: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True)
    raw_time: so.Mapped[float] = so.mapped_column(sa.Numeric(5,2), index=True)
    adjusted_time: so.Mapped[float] = so.mapped_column(sa.Numeric(5,2), index=True)
    