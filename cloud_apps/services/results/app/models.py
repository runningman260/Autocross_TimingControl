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

def get_available_databases():
    """Query PostgreSQL for available databases using SQLAlchemy"""
    try:
        result = db.session.execute(sa.text("SELECT datname FROM pg_database WHERE datistemplate = false;"))
        databases = [row[0] for row in result.fetchall()]
        return [db for db in databases if db != 'postgres']
    except Exception as e:
        current_app.logger.error(f"Error fetching databases: {e}")
        return []

def get_runs_from_database(database_name, table_name, page=1, per_page=10, team_id=None):
    """Query runs from a specific database and table with pagination, team info, and optional team filter"""
    try:
        offset = (page - 1) * per_page
        where_clause = f"WHERE t.id = {team_id}" if team_id else ""
        query = sa.text(f"""
            SELECT r.*, t.name as team_name, t.abbreviation as team_abbreviation
            FROM {table_name} r
            LEFT JOIN carreg c ON r.car_number = c.car_number
            LEFT JOIN team t ON c.team_id = t.id
            {where_clause}
            ORDER BY r.id DESC
            LIMIT {per_page} OFFSET {offset}
        """)
        result = db.session.execute(query)
        
        runs = []
        for row in result.fetchall():
            run_dict = dict(row._mapping)
            runs.append(type('Run', (), run_dict)())
        
        return runs
    except Exception as e:
        current_app.logger.error(f"Error fetching runs from {database_name}.{table_name}: {e}")
        return []

def get_teams_from_database():
    """Get all teams from the database"""
    try:
        query = sa.text("SELECT id, name FROM team ORDER BY name")
        result = db.session.execute(query)
        teams = []
        for row in result.fetchall():
            teams.append(type('Team', (), {'id': row[0], 'name': row[1]})())
        return teams
    except Exception as e:
        current_app.logger.error(f"Error fetching teams: {e}")
        return []

##Events
