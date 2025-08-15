from datetime import datetime, timezone, timedelta
import os
import requests
from flask import  request, jsonify, render_template, redirect, url_for, flash, session
from flask_babel import _
import sqlalchemy as sa
from app import db
from app.models import News
from app.main import bp
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
import csv
from io import StringIO


@bp.route('/', methods=['GET', 'POST']) #fix for form not working without explicit path specified - needs post method allowed for root path 
def landingpage():
    latest_news = db.session.scalars(sa.select(News).order_by(News.created_at.desc()).limit(1)).first()
    
    # Example coordinates (replace with your event location)
    # Pittsburgh, PA coordinates
    weather = get_current_weather(40.8486,-80.3454)
    
    return render_template('landingpage.html', latest_news=latest_news, weather=weather, timezone=timezone, timedelta=timedelta)

def get_current_weather(lat, lon):
    """Get current weather and 3-hour forecast from NWS API using lat/lon coordinates"""
    try:
        # Step 1: Get grid coordinates from lat/lon
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        points_response = requests.get(points_url, timeout=10)
        points_response.raise_for_status()
        points_data = points_response.json()
        
        # Step 2: Get nearest weather station for current conditions
        stations_url = points_data['properties']['observationStations']
        stations_response = requests.get(stations_url, timeout=10)
        stations_response.raise_for_status()
        stations_data = stations_response.json()
        
        current_weather = None
        if stations_data['features']:
            # Step 3: Get current conditions from first station
            station_id = stations_data['features'][0]['properties']['stationIdentifier']
            current_url = f"https://api.weather.gov/stations/{station_id}/observations/latest"
            current_response = requests.get(current_url, timeout=10)
            current_response.raise_for_status()
            current_data = current_response.json()
            
            properties = current_data['properties']
            
            # Convert temperature from Celsius to Fahrenheit
            temp_c = properties.get('temperature', {}).get('value')
            temp_f = round(temp_c * 9/5 + 32) if temp_c else None
            
            current_weather = {
                'temperature': temp_f,
                'description': properties.get('textDescription', 'N/A'),
                'humidity': properties.get('relativeHumidity', {}).get('value'),
                'wind_speed': properties.get('windSpeed', {}).get('value'),
                'wind_direction': properties.get('windDirection', {}).get('value')
            }
        
        # Step 4: Get hourly forecast
        forecast_hourly_url = points_data['properties']['forecastHourly']
        forecast_response = requests.get(forecast_hourly_url, timeout=10)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()
        
        # Get next 3 hours of forecast
        forecast_3h = []
        for period in forecast_data['properties']['periods'][:3]:
            # Parse hour from startTime (e.g., "2024-01-15T14:00:00-05:00")
            start_time = datetime.fromisoformat(period['startTime'].replace('Z', '+00:00'))
            hour_display = start_time.strftime('%I %p').lstrip('0')  # Format as "2 PM"
            
            forecast_3h.append({
                'time': period['name'],
                'hour': hour_display,
                'temperature': period['temperature'],
                'description': period['shortForecast'],
                'wind_speed': period.get('windSpeed', 'N/A'),
                'wind_direction': period.get('windDirection', 'N/A')
            })
        
        return {
            'current': current_weather,
            'forecast_3h': forecast_3h
        }
        
    except Exception as e:
        print(f"Weather API error: {e}")
        return None

@bp.route('/news', methods=['GET'])
def news():
    news_items = db.session.scalars(sa.select(News).order_by(News.created_at.desc())).all()
    return render_template('news.html', title='News', news_items=news_items, timezone=timezone, timedelta=timedelta)
