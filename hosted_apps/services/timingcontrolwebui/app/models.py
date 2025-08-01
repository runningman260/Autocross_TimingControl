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

class RunOrder(db.Model):
    __tablename__ = 'runtable'
    id: so.Mapped[int] = so.mapped_column(primary_key=True, autoincrement=True)
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    cones: so.Mapped[int] = so.mapped_column(sa.String(128), nullable=True) 
    off_course: so.Mapped[int] = so.mapped_column(sa.String(128), nullable=True)
    dnf: so.Mapped[str] = so.mapped_column(sa.String(128))
    raw_time: so.Mapped[float] = so.mapped_column(sa.String(128))
    adjusted_time: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    startline_scan_status: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    finishline_scan_status: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False, default=datetime.now) 
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False, default=datetime.now)    
    last_synced_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=True) 
    
    def __repr__(self):
        return '<RunOrder {}>'.format(self.id)
    
    def print_row(self):
        return f'{self.id}; {self.car_number}; {self.cones}; {self.off_course}; {self.dnf}; {self.raw_time}; {self.adjusted_time};'

class Accel_RunOrder(db.Model):
    __tablename__ = 'accel_runtable'
    id: so.Mapped[int] = so.mapped_column(primary_key=True, autoincrement=True)
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    cones: so.Mapped[int] = so.mapped_column(sa.String(128), nullable=True) 
    off_course: so.Mapped[int] = so.mapped_column(sa.String(128), nullable=True)
    dnf: so.Mapped[str] = so.mapped_column(sa.String(128))
    raw_time: so.Mapped[str] = so.mapped_column(sa.String(128))
    adjusted_time: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False, default=datetime.now) 
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False, default=datetime.now)    
    last_synced_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=True) 
    
    def __repr__(self):
        return '<Accel_RunOrder {}>'.format(self.id)
    
    def print_row(self):
        return f'{self.id}; {self.car_number}; {self.cones}; {self.off_course}; {self.dnf}; {self.raw_time}; {self.adjusted_time};'

class Skidpad_RunOrder(db.Model):
    __tablename__ = 'skidpad_runtable'
    id: so.Mapped[int] = so.mapped_column(primary_key=True, autoincrement=True)
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    cones: so.Mapped[int] = so.mapped_column(sa.String(128), nullable=True) 
    off_course: so.Mapped[int] = so.mapped_column(sa.String(128), nullable=True)
    dnf: so.Mapped[str] = so.mapped_column(sa.String(128))
    raw_time_left: so.Mapped[str] = so.mapped_column(sa.String(128))
    raw_time_right: so.Mapped[str] = so.mapped_column(sa.String(128))
    adjusted_time: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False, default=datetime.now) 
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False, default=datetime.now)    
    last_synced_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=True) 
    
    def __repr__(self):
        return '<Skidpad_RunOrder {}>'.format(self.id)
    
    def print_row(self):
        return f'{self.id}; {self.car_number}; {self.cones}; {self.off_course}; {self.dnf}; {self.raw_time_left}; {self.raw_time_right}; {self.adjusted_time};'

class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    abbreviation = db.Column(db.String(16), unique=True, nullable=False)
    car_regs = db.relationship("CarReg", back_populates="team")

class CarReg(db.Model):
    __tablename__ = 'carreg'
    id: so.Mapped[int] = so.mapped_column(primary_key=True, autoincrement=True)
    scan_time: so.Mapped[datetime] = so.mapped_column(sa.DateTime)
    tag_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True, unique=True)
    team_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('team.id'), index=True)
    team = so.relationship("Team", back_populates="car_regs")
    class_: so.Mapped[str] = so.mapped_column(sa.String(128), index=True, name='class')
    year: so.Mapped[str] = so.mapped_column(sa.String(16))
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False, default=datetime.now)
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return '<CarReg {}>'.format(self.id)

## LapTime Leaderboards
class Autocross_TopLaps(db.Model):
    __tablename__ = 'autocross_leaderboard'
    __table_args__ = {'info': {'is_view': True}}
    __mapper_args__ = {'primary_key': ['car_number', 'adjusted_time', 'team_name']}
      
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    team_name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    adjusted_time: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    cones: so.Mapped[int] = so.mapped_column(sa.Integer)
    off_course: so.Mapped[int] = so.mapped_column(sa.Integer)
    id: so.Mapped[int] = so.mapped_column(sa.Integer)
    class_: so.Mapped[str] = so.mapped_column(sa.String(128), index=True, name='class')

class Accel_TopLaps(db.Model):
    __tablename__ = 'accel_leaderboard'
    __table_args__ = {'info': {'is_view': True}}
    __mapper_args__ = {'primary_key': ['car_number', 'adjusted_time', 'team_name']}
      
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    team_name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    adjusted_time: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    cones: so.Mapped[int] = so.mapped_column(sa.Integer)
    off_course: so.Mapped[int] = so.mapped_column(sa.Integer)
    id: so.Mapped[int] = so.mapped_column(sa.Integer)
    class_: so.Mapped[str] = so.mapped_column(sa.String(128), index=True, name='class')

class Skidpad_TopLaps(db.Model):
    __tablename__ = 'skidpad_leaderboard'
    __table_args__ = {'info': {'is_view': True}}
    __mapper_args__ = {'primary_key': ['car_number', 'adjusted_time', 'team_name']}
      
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    team_name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    adjusted_time: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    cones: so.Mapped[int] = so.mapped_column(sa.Integer)
    off_course: so.Mapped[int] = so.mapped_column(sa.Integer)
    id: so.Mapped[int] = so.mapped_column(sa.Integer)
    class_: so.Mapped[str] = so.mapped_column(sa.String(128), index=True, name='class')

# Points-tracking leaderboards
class Autocross_PointsLeaderboardIC(db.Model):
    __tablename__ = 'autocross_points_leaderboard_ic'
    __table_args__ = {'info': {'is_view': True}}
    __mapper_args__ = {'primary_key': ['car_number', 'adjusted_time', 'points']}
       
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    adjusted_time: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    points: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    team_name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    
class Autocross_PointsLeaderboardEV(db.Model):
    __tablename__ = 'autocross_points_leaderboard_ev'
    __table_args__ = {'info': {'is_view': True}}
    __mapper_args__ = {'primary_key': ['car_number', 'adjusted_time', 'points']}
       
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    adjusted_time: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    points: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    team_name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)

class Accel_PointsLeaderboardIC(db.Model):
    __tablename__ = 'accel_points_leaderboard_ic'
    __table_args__ = {'info': {'is_view': True}}
    __mapper_args__ = {'primary_key': ['car_number', 'adjusted_time', 'points']}
       
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    adjusted_time: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    points: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    team_name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    
class Accel_PointsLeaderboardEV(db.Model):
    __tablename__ = 'accel_points_leaderboard_ev'
    __table_args__ = {'info': {'is_view': True}}
    __mapper_args__ = {'primary_key': ['car_number', 'adjusted_time', 'points']}
       
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    adjusted_time: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    points: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    team_name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    
class Skidpad_PointsLeaderboardIC(db.Model):
    __tablename__ = 'skidpad_points_leaderboard_ic'
    __table_args__ = {'info': {'is_view': True}}
    __mapper_args__ = {'primary_key': ['car_number', 'adjusted_time', 'points']}
       
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    adjusted_time: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    points: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    team_name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    
class Skidpad_PointsLeaderboardEV(db.Model):
    __tablename__ = 'skidpad_points_leaderboard_ev'
    __table_args__ = {'info': {'is_view': True}}
    __mapper_args__ = {'primary_key': ['car_number', 'adjusted_time', 'points']}
       
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    adjusted_time: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    points: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    team_name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)  

class Overall_PointsLeaderboardIC(db.Model):
    __tablename__ = 'overall_points_leaderboard_ic'
    __table_args__ = {'info': {'is_view': True}}
    __mapper_args__ = {'primary_key': ['car_number', 'autocross_points', 'accel_points', 'skidpad_points', 'total_points']}
        
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    autocross_points: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    accel_points: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    skidpad_points: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    total_points: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    team_name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)   
    
class Overall_PointsLeaderboardEV(db.Model):
    __tablename__ = 'overall_points_leaderboard_ev'
    __table_args__ = {'info': {'is_view': True}}
    __mapper_args__ = {'primary_key': ['car_number', 'autocross_points', 'accel_points', 'skidpad_points', 'total_points']}
        
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    autocross_points: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    accel_points: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    skidpad_points: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    total_points: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    team_name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)   
    
# Conekiller  
class ConesLeaderboard(db.Model):
    __tablename__ = 'cones_leaderboard'
    __table_args__ = {'info': {'is_view': True}}
    __mapper_args__ = {'primary_key': ['car_number', 'autocross_cones', 'accel_cones', 'skidpad_cones', 'total_cones']}
       
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    autocross_cones: so.Mapped[int] = so.mapped_column(sa.Integer, index=True)
    accel_cones: so.Mapped[int] = so.mapped_column(sa.Integer, index=True)
    skidpad_cones: so.Mapped[int] = so.mapped_column(sa.Integer, index=True)
    total_cones: so.Mapped[int] = so.mapped_column(sa.Integer, index=True)
    team_name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)


