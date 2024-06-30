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


class RunOrder(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    team_name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    location: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    tag: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    car_number: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    cones: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    off_courses: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    raw_time: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    adjusted_time: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    
    def __repr__(self):
        return '<RunOrder {}>'.format(self.id)
    
    # This is dumb, need to find a better way
    def print_row(self):
        return '{}; {}; {}; {}; {}; {}; {}; {}; {};'.format(self.id, self.team_name, self.location, self.tag, self.car_number, self.cones, self.off_courses, self.raw_time, self.adjusted_time)
