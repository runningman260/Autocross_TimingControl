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

##Events
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
    raw_time: so.Mapped[float] = so.mapped_column(sa.String(128))
    adjusted_time: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False, default=datetime.now)
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False, default=datetime.now)
    last_synced_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=True)

class Skidpad_RunOrder(db.Model):
    __tablename__ = 'skidpad_runtable'
    id: so.Mapped[int] = so.mapped_column(primary_key=True, autoincrement=True)
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    cones: so.Mapped[int] = so.mapped_column(sa.String(128), nullable=True)
    off_course: so.Mapped[int] = so.mapped_column(sa.String(128), nullable=True)
    dnf: so.Mapped[str] = so.mapped_column(sa.String(128))
    raw_time_left: so.Mapped[float] = so.mapped_column(sa.String(128))
    raw_time_right: so.Mapped[float] = so.mapped_column(sa.String(128))
    adjusted_time: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False, default=datetime.now)
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False, default=datetime.now)
    last_synced_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=True)

## Other Structure
class Team(db.Model):
    __tablename__ = 'team'
    id: so.Mapped[int] = so.mapped_column(primary_key=True, autoincrement=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(128), unique=True, nullable=False)
    abbreviation: so.Mapped[str] = so.mapped_column(sa.String(16), unique=True, nullable=False)
    car_regs = so.relationship("CarReg", back_populates="team")

    def __repr__(self):
        return f"<Team {self.id} {self.name}>"

class CarReg(db.Model):
    __tablename__ = 'carreg'
    id: so.Mapped[int] = so.mapped_column(primary_key=True, autoincrement=True)
    scan_time: so.Mapped[datetime] = so.mapped_column(sa.DateTime)
    tag_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True, unique=True)
    team_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('team.id'), index=True)
    team = so.relationship("Team", back_populates="car_regs")
    class_: so.Mapped[str] = so.mapped_column(sa.String(128), index=True, name='class')
    year: so.Mapped[str] = so.mapped_column(sa.String(4))

    def __repr__(self):
        return '<CarReg {}>'.format(self.id)