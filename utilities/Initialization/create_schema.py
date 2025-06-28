#/bin/python3

#######################################################################################
#                                                                                     #
#  Task to generate the schema for the Shootout database.                             #
#  Includes a switch to delete all the previous information as well.                  #
#                                                                                     #
############################################################ Pittsburgh Shootout LLC ##

import os, sys
import time
import atexit
from config import Config
from database_helper import *
import paho.mqtt.client as paho
import json
import datetime

def exit_handler():
	print(' Cleaning Up!')
	exit(1)

clear_and_create_schema()

#create_view and create_table are identical lol

# Create Leaderboard based on Adjusted_time
print("Creating Leaderboard")
sql = """
CREATE OR REPLACE VIEW leaderboard AS
SELECT
    runtable.car_number,
    team.name AS team_name,
    team.abbreviation AS team_abbreviation,
    runtable.adjusted_time,
    runtable.cones,
    runtable.off_course,
    runtable.id,
    carreg.class
FROM runtable
JOIN carreg ON runtable.car_number = carreg.car_number
LEFT JOIN team ON carreg.team_id = team.id
WHERE
    adjusted_time IS NOT NULL
    AND adjusted_time IS DISTINCT FROM 'DNF'
    AND raw_time IS NOT NULL
    AND (raw_time::decimal > 0)
ORDER BY
    CASE WHEN pg_input_is_valid(adjusted_time, 'decimal') THEN adjusted_time::decimal END ASC;
"""
create_view(sql)

# Create Points Leaderboard based on 2024 SAE Autocross score calc
print("Creating IC Points Leaderboard")
sql = """
CREATE OR REPLACE VIEW points_leaderboard_ic AS
SELECT
    c.car_number,
    c.team_name,
    c.team_abbreviation,
    c.adjusted_time,
    c.points
FROM (
    SELECT DISTINCT ON (b.car_number::int)
        b.car_number,
        b.team_name,
        b.team_abbreviation,
        b.adjusted_time,
        b.points
    FROM (
        SELECT
            s.car_number,
            s.team_name,
            s.team_abbreviation,
            s.adjusted_time,
            s.tmin AS MIN,
            s.tmax AS max,
            CASE
                WHEN s.adjusted_time::decimal > s.tmax::decimal THEN 6.5
                ELSE trunc((118.5 * ((s.tmax::decimal / s.adjusted_time::decimal) - 1) / ((s.tmax::decimal / s.tmin::decimal) - 1)) + 6.5, 3)
            END AS points
        FROM (
            SELECT
                runtable.car_number,
                runtable.adjusted_time,
                runtable.raw_time,
                MIN(adjusted_time::decimal) OVER () AS tmin,
                1.45 * MIN(adjusted_time::decimal) OVER () AS tmax,
                team.name AS team_name,
                team.abbreviation AS team_abbreviation
            FROM runtable
            JOIN carreg ON runtable.car_number = carreg.car_number
            LEFT JOIN team ON carreg.team_id = team.id
            WHERE carreg.class = 'IC'
                AND adjusted_time IS NOT NULL
                AND adjusted_time IS DISTINCT FROM 'DNF'
                AND raw_time IS NOT NULL
                AND (raw_time::decimal > 0)
        ) s
        ORDER BY points DESC
    ) b
    ORDER BY b.car_number::int, b.points DESC
) c
ORDER BY c.points DESC;
"""
create_view(sql)

print("Creating EV Points Leaderboard")
sql = """
CREATE OR REPLACE VIEW points_leaderboard_ev AS
SELECT
    c.car_number,
    c.team_name,
    c.team_abbreviation,
    c.adjusted_time,
    c.points
FROM (
    SELECT DISTINCT ON (b.car_number::int)
        b.car_number,
        b.team_name,
        b.team_abbreviation,
        b.adjusted_time,
        b.points
    FROM (
        SELECT
            s.car_number,
            s.team_name,
            s.team_abbreviation,
            s.adjusted_time,
            s.tmin AS MIN,
            s.tmax AS max,
            CASE
                WHEN s.adjusted_time::decimal > s.tmax::decimal THEN 6.5
                ELSE trunc((118.5 * ((s.tmax::decimal / s.adjusted_time::decimal) - 1) / ((s.tmax::decimal / s.tmin::decimal) - 1)) + 6.5, 3)
            END AS points
        FROM (
            SELECT
                runtable.car_number,
                runtable.adjusted_time,
                runtable.raw_time,
                MIN(adjusted_time::decimal) OVER () AS tmin,
                1.45 * MIN(adjusted_time::decimal) OVER () AS tmax,
                team.name AS team_name,
                team.abbreviation AS team_abbreviation
            FROM runtable
            JOIN carreg ON runtable.car_number = carreg.car_number
            LEFT JOIN team ON carreg.team_id = team.id
            WHERE carreg.class = 'EV'
                AND adjusted_time IS NOT NULL
                AND adjusted_time IS DISTINCT FROM 'DNF'
                AND raw_time IS NOT NULL
                AND (raw_time::decimal > 0)
        ) s
        ORDER BY points DESC
    ) b
    ORDER BY b.car_number::int, b.points DESC
) c
ORDER BY c.points DESC;
"""
create_view(sql)

# Create Cones Leaderboard
print("Creating Cones Leaderboard")
sql = """
CREATE OR REPLACE VIEW cones_leaderboard AS
SELECT
    runtable.car_number,
    team.name AS team_name,
    team.abbreviation AS team_abbreviation,
    SUM(runtable.cones::int) AS total_cones
FROM runtable
JOIN carreg ON runtable.car_number = carreg.car_number
LEFT JOIN team ON carreg.team_id = team.id
WHERE
    runtable.adjusted_time IS NOT NULL
    AND runtable.cones IS NOT NULL
    AND (runtable.cones::numeric > 0)
GROUP BY
    runtable.car_number,
    team.name,
    team.abbreviation
ORDER BY
    total_cones DESC;
"""
create_view(sql)

