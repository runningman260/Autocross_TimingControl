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

## Creating Laptime Leaderboard for each event
# Autocross leaderboard entry below is 'blank' so that the view and table names are maintained
# (legacy autocross table names don't have an event prefix) <- This should change for 2026
laptime_leaderboard_events = ["","accel_","skidpad_"]
for event in laptime_leaderboard_events:
    if event == "":
        event_name = "autocross_"
    else:
        event_name = event
    print(f"Creating {event_name} LapTimes Leaderboard")

    sql = """
    CREATE OR REPLACE VIEW {event_name}leaderboard AS
    SELECT
        {event}runtable.car_number,
        team.name AS team_name,
        team.abbreviation AS team_abbreviation,
        {event}runtable.adjusted_time,
        {event}runtable.cones,
        {event}runtable.off_course,
        {event}runtable.id,
        carreg.class
    FROM {event}runtable
    JOIN carreg ON {event}runtable.car_number = carreg.car_number
    LEFT JOIN team ON carreg.team_id = team.id
    WHERE
        adjusted_time IS NOT NULL
        AND adjusted_time IS DISTINCT FROM 'DNF'
        AND raw_time{skidpad_string} IS NOT NULL
        AND (raw_time{skidpad_string}::decimal > 0)
    ORDER BY
        CASE WHEN pg_input_is_valid(adjusted_time, 'decimal') THEN adjusted_time::decimal END ASC;
    """.format(event=event, skidpad_string="_left" if event=="skidpad_" else "")
    create_view(sql)

## AUTOCROSS POINTS TRACKER
# 'leaderboards' based on actual competition scoring
# Calling it a tracker to give a distinction between leaderboards and trackers for sanity
points_tracker_classes = ["IC","EV"]
for car_class in points_tracker_classes:
    print(f"Creating {car_class} Points Tracker for Autocross")

    sql = """
    CREATE OR REPLACE VIEW autocross_points_leaderboard_{car_class_lower} AS
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
                WHERE carreg.class = '{car_class}'
                    AND adjusted_time IS NOT NULL
                    AND adjusted_time IS DISTINCT FROM 'DNF'
                    AND raw_time IS NOT NULL
                    AND (raw_time::decimal > 0)
            ) s
            ORDER BY points DESC
        ) b
        ORDER BY b.car_number::int, b.points DESC
    ) c
    ORDER BY c.points DESC, adjusted_time::decimal ASC;
    """.format(car_class=car_class, car_class_lower=car_class.lower())
    create_view(sql)

## ACCEL POINTS TRACKER
for car_class in points_tracker_classes:
    print(f"Creating {car_class} Points Tracker for Acceleration")

    sql = """
    CREATE OR REPLACE VIEW accel_points_leaderboard_{car_class_lower} AS
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
                    WHEN s.adjusted_time::decimal > s.tmax::decimal THEN 4.5
                    ELSE trunc((95.5 * ((s.tmax::decimal / s.adjusted_time::decimal) - 1) / ((s.tmax::decimal / s.tmin::decimal) - 1)) + 4.5, 3)
                END AS points
            FROM (
                SELECT
                    accel_runtable.car_number,
                    accel_runtable.adjusted_time,
                    accel_runtable.raw_time,
                    MIN(adjusted_time::decimal) OVER () AS tmin,
                    1.5 * MIN(adjusted_time::decimal) OVER () AS tmax,
                    team.name AS team_name,
                    team.abbreviation AS team_abbreviation
                FROM accel_runtable
                JOIN carreg ON accel_runtable.car_number = carreg.car_number
                LEFT JOIN team ON carreg.team_id = team.id
                WHERE carreg.class = '{car_class}'
                    AND adjusted_time IS NOT NULL
                    AND adjusted_time IS DISTINCT FROM 'DNF'
                    AND raw_time IS NOT NULL
                    AND (raw_time::decimal > 0)
            ) s
            ORDER BY points DESC
        ) b
        ORDER BY b.car_number::int, b.points DESC
    ) c
    ORDER BY c.points DESC, adjusted_time::decimal ASC;
    """.format(car_class=car_class, car_class_lower=car_class.lower())
    create_view(sql)

## SKIDPAD POINTS TRACKER
for car_class in points_tracker_classes:
    print(f"Creating {car_class} Points Tracker for Skidpad")

    sql = """
    CREATE OR REPLACE VIEW skidpad_points_leaderboard_{car_class_lower} AS
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
                    WHEN s.adjusted_time::decimal > s.tmax::decimal THEN 3.5
                    ELSE trunc((71.5 * ((((s.tmax::decimal / s.adjusted_time::decimal) * (s.tmax::decimal / s.adjusted_time::decimal)) - 1) / (((s.tmax::decimal / s.tmin::decimal) * (s.tmax::decimal / s.tmin::decimal)) - 1))) + 3.5, 3)
                END AS points
            FROM (
                SELECT
                    skidpad_runtable.car_number,
                    skidpad_runtable.adjusted_time,
                    skidpad_runtable.raw_time_left,
                    skidpad_runtable.raw_time_right,
                    MIN(adjusted_time::decimal) OVER () AS tmin,
                    1.25 * MIN(adjusted_time::decimal) OVER () AS tmax,
                    team.name AS team_name,
                    team.abbreviation AS team_abbreviation
                FROM skidpad_runtable
                JOIN carreg ON skidpad_runtable.car_number = carreg.car_number
                LEFT JOIN team ON carreg.team_id = team.id
                WHERE carreg.class = '{car_class}'
                    AND adjusted_time IS NOT NULL
                    AND adjusted_time IS DISTINCT FROM 'DNF'
                    AND raw_time_left IS NOT NULL
                    AND raw_time_right IS NOT NULL
                    AND (raw_time_left::decimal > 0)
                    AND (raw_time_right::decimal > 0)
            ) s
            ORDER BY points DESC
        ) b
        ORDER BY b.car_number::int, b.points DESC
    ) c
    ORDER BY c.points DESC, adjusted_time::decimal ASC;
    """.format(car_class=car_class, car_class_lower=car_class.lower())
    create_view(sql)

# Overall points leaderboard (EV and IC)
print("Creating Overall Points Leaderboard")
sql = """
CREATE OR REPLACE VIEW overall_points_leaderboard AS
SELECT
    car_number,
    team_name,
    team_abbreviation,
    SUM(points) AS total_points
FROM (
    SELECT car_number, team_name, team_abbreviation, points FROM autocross_points_leaderboard_ic
    UNION ALL
    SELECT car_number, team_name, team_abbreviation, points FROM autocross_points_leaderboard_ev
    UNION ALL
    SELECT car_number, team_name, team_abbreviation, points FROM accel_points_leaderboard_ic
    UNION ALL
    SELECT car_number, team_name, team_abbreviation, points FROM accel_points_leaderboard_ev
    UNION ALL
    SELECT car_number, team_name, team_abbreviation, points FROM skidpad_points_leaderboard_ic
    UNION ALL
    SELECT car_number, team_name, team_abbreviation, points FROM skidpad_points_leaderboard_ev
) combined_points
GROUP BY
    car_number,
    team_name,
    team_abbreviation
ORDER BY
    total_points DESC;
"""
create_view(sql)

# Create Cones Leaderboard
print("Creating Cones Leaderboard")
sql = """
CREATE OR REPLACE VIEW cones_leaderboard AS
SELECT
    car_number,
    team_name,
    team_abbreviation,
    SUM(cones::int) AS total_cones
FROM (
    SELECT
        runtable.car_number,
        team.name AS team_name,
        team.abbreviation AS team_abbreviation,
        runtable.cones
    FROM runtable
    JOIN carreg ON runtable.car_number = carreg.car_number
    LEFT JOIN team ON carreg.team_id = team.id
    WHERE
        runtable.adjusted_time IS NOT NULL
        AND runtable.cones IS NOT NULL
        AND (runtable.cones::numeric > 0)
    
    UNION ALL
    
    SELECT
        accel_runtable.car_number,
        team.name AS team_name,
        team.abbreviation AS team_abbreviation,
        accel_runtable.cones
    FROM accel_runtable
    JOIN carreg ON accel_runtable.car_number = carreg.car_number
    LEFT JOIN team ON carreg.team_id = team.id
    WHERE
        accel_runtable.adjusted_time IS NOT NULL
        AND accel_runtable.cones IS NOT NULL
        AND (accel_runtable.cones::numeric > 0)
    
    UNION ALL
    
    SELECT
        skidpad_runtable.car_number,
        team.name AS team_name,
        team.abbreviation AS team_abbreviation,
        skidpad_runtable.cones
    FROM skidpad_runtable
    JOIN carreg ON skidpad_runtable.car_number = carreg.car_number
    LEFT JOIN team ON carreg.team_id = team.id
    WHERE
        skidpad_runtable.adjusted_time IS NOT NULL
        AND skidpad_runtable.cones IS NOT NULL
        AND (skidpad_runtable.cones::numeric > 0)
) combined_cones
GROUP BY
    car_number,
    team_name,
    team_abbreviation
ORDER BY
    total_cones DESC;
"""
create_view(sql)