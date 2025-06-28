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

#clear_and_create_schema()

# Create Leaderboard based on Adjusted_time
print("Creating Leaderboard")
sql = """
create or replace view leaderboard as 
    Select runtable.car_number, carreg.team_name, runtable.adjusted_time, runtable.cones, runtable.off_course, runtable.id, carreg.class
from runtable 
join carreg on runtable.car_number=carreg.car_number 
where adjusted_time is not null and adjusted_time is distinct from 'DNF' and raw_time is not null and (raw_time::decimal > 0)
ORDER BY CASE WHEN pg_input_is_valid(adjusted_time, 'decimal') THEN adjusted_time::decimal END asc;
"""
create_view(sql)

# Create Points Leaderboard based on 2024 SAE Autocross score calc
print("Creating IC Points Leaderboard")
sql = """
create or replace view points_leaderboard_ic as
select c.car_number, c.team_name, c.adjusted_time, c.points
from (
    select
    distinct on (b.car_number::int) b.car_number, b.team_name, b.adjusted_time, b.points
    from (
        select 
            s.car_number, 
			s.team_name,
            s.adjusted_time, 
            s.tmin as MIN,
            s.tmax as max,
            case 
                when s.adjusted_time::decimal > s.tmax::decimal then 6.5
                else trunc((118.5*((s.tmax::decimal/s.adjusted_time::decimal)-1)/((s.tmax::decimal/ s.tmin::decimal)-1))+6.5, 3)
            end as points
            from (
                select
                    runtable.car_number, runtable.adjusted_time, runtable.raw_time,
                    min(adjusted_time::decimal) over () as tmin,
                    1.45*min(adjusted_time::decimal) over () as Tmax,
					carreg.team_name
                    from runtable
					join carreg on runtable.car_number=carreg.car_number 
					where carreg.class = 'IC' and adjusted_time is not null and adjusted_time is distinct from 'DNF' and raw_time is not null and (raw_time::decimal > 0)
                ) s
        order by points desc
        ) b
    order by b.car_number::int, b.points desc
    ) c
order by c.points desc;
"""
create_view(sql)

print("Creating EV Points Leaderboard")
sql = """
create or replace view points_leaderboard_ev as
select c.car_number, c.team_name, c.adjusted_time, c.points
from (
    select
    distinct on (b.car_number::int) b.car_number, b.team_name, b.adjusted_time, b.points
    from (
        select 
            s.car_number, 
			s.team_name,
            s.adjusted_time, 
            s.tmin as MIN,
            s.tmax as max,
            case 
                when s.adjusted_time::decimal > s.tmax::decimal then 6.5
                else trunc((118.5*((s.tmax::decimal/s.adjusted_time::decimal)-1)/((s.tmax::decimal/ s.tmin::decimal)-1))+6.5, 3)
            end as points
            from (
                select
                    runtable.car_number, runtable.adjusted_time, runtable.raw_time,
                    min(adjusted_time::decimal) over () as tmin,
                    1.45*min(adjusted_time::decimal) over () as Tmax,
					carreg.team_name
                    from runtable
					join carreg on runtable.car_number=carreg.car_number 
					where carreg.class = 'EV' and adjusted_time is not null and adjusted_time is distinct from 'DNF' and raw_time is not null and (raw_time::decimal > 0)
                ) s
        order by points desc
        ) b
    order by b.car_number::int, b.points desc
    ) c
order by c.points desc;
"""
create_view(sql)

# Create Cones Leaderboard
print("Creating Cones Leaderboard")
sql = """
CREATE or REPLACE VIEW cones_leaderboard
AS
( SELECT 
    runtable.car_number,
    carreg.team_name,
    SUM(runtable.cones::int) as total_cones    
   FROM (runtable
     JOIN carreg ON (((runtable.car_number)::text = (carreg.car_number)::text)))
   WHERE (
     (runtable.adjusted_time IS NOT NULL) 
      AND 
     (runtable.cones IS NOT NULL) 
	  AND 
	 (runtable.cones::numeric > 0) 
   )
  GROUP BY runtable.car_number, carreg.team_name
  ORDER BY
        total_cones DESC)
"""
create_view(sql)

