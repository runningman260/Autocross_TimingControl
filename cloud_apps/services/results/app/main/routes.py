from datetime import datetime, timezone
import os
from flask import  request, jsonify, render_template, redirect, url_for, flash, session
from flask_babel import _
import sqlalchemy as sa
from app import db
from app.main import bp
from app.forms import DatabaseSelectForm
from app.models import get_available_databases, get_runs_from_database, get_teams_from_database
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
import csv
from io import StringIO


@bp.route('/', methods=['GET', 'POST']) #fix for form not working without explicit path specified - needs post method allowed for root path 
def results():
    form = DatabaseSelectForm()
    
    # Populate dropdown choices using models function
    databases = get_available_databases()
    form.database.choices = [(db, db) for db in databases]
    
    selected_database = None
    selected_team_id = None
    autocross_runs = []
    accel_runs = []
    skidpad_runs = []
    teams = []
    autocross_page = 1
    accel_page = 1
    skidpad_page = 1
    
    # Check if team changed to reset pagination
    team_changed = False
    if form.validate_on_submit():
        selected_database = form.database.data
        selected_team_id = request.form.get('team_id')
        if session.get('selected_team_id') != selected_team_id:
            team_changed = True
        session['selected_database'] = selected_database
        session['selected_team_id'] = selected_team_id
    elif 'selected_database' in session:
        selected_database = session['selected_database']
        selected_team_id = session.get('selected_team_id')
        form.database.data = selected_database
    
    if selected_database:
        # Get teams and page numbers (reset to 1 if team changed)
        teams = get_teams_from_database()
        autocross_page = 1 if team_changed else request.args.get('autocross_page', 1, type=int)
        accel_page = 1 if team_changed else request.args.get('accel_page', 1, type=int)
        skidpad_page = 1 if team_changed else request.args.get('skidpad_page', 1, type=int)
        
        try:
            autocross_runs = get_runs_from_database(selected_database, 'runtable', autocross_page, 10, selected_team_id)
            accel_runs = get_runs_from_database(selected_database, 'accel_runtable', accel_page, 10, selected_team_id)
            skidpad_runs = get_runs_from_database(selected_database, 'skidpad_runtable', skidpad_page, 10, selected_team_id)
        except Exception as e:
            flash(f'Error accessing database {selected_database}: {e}', 'error')
    
    return render_template('results.html', form=form, selected_database=selected_database,
                         autocross_runs=autocross_runs, accel_runs=accel_runs, skidpad_runs=skidpad_runs,
                         autocross_page=autocross_page, accel_page=accel_page, skidpad_page=skidpad_page,
                         teams=teams, selected_team_id=selected_team_id)

@bp.route('/export/<table>')
def export_csv(table):
    selected_team_id = session.get('selected_team_id')
    selected_database = session.get('selected_database')
    
    if not selected_team_id or not selected_database:
        flash('Please select a team and database to export data', 'error')
        return redirect(url_for('main.results'))
    
    # Map table names to database table names
    table_map = {
        'autocross': 'runtable',
        'acceleration': 'accel_runtable', 
        'skidpad': 'skidpad_runtable'
    }
    
    if table not in table_map:
        flash('Invalid table specified', 'error')
        return redirect(url_for('main.results'))
    
    # Get all runs for the team (no pagination) and team info
    runs = get_runs_from_database(selected_database, table_map[table], 1, 10000, selected_team_id)
    
    # Get team abbreviation from first run or fetch separately
    team_abbr = 'unknown'
    if runs and hasattr(runs[0], 'team_abbreviation') and runs[0].team_abbreviation:
        team_abbr = runs[0].team_abbreviation.lower()
    
    # Generate CSV content
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write headers based on table type
    if table == 'skidpad':
        writer.writerow(['Run #', 'Car #', 'Team', 'Cones', 'Off Course', 'DNF', 'Raw Time Left', 'Raw Time Right', 'Adjusted Time'])
        for run in runs:
            writer.writerow([run.id, run.car_number, run.team_name or 'Unknown', run.cones or 0, run.off_course or 0, run.dnf, run.raw_time_left, run.raw_time_right, run.adjusted_time])
    else:
        writer.writerow(['Run #', 'Car #', 'Team', 'Cones', 'Off Course', 'DNF', 'Raw Time', 'Adjusted Time'])
        for run in runs:
            writer.writerow([run.id, run.car_number, run.team_name or 'Unknown', run.cones or 0, run.off_course or 0, run.dnf, run.raw_time, run.adjusted_time])
    
    # Create filename: {competition}_{event}_results_{team_abbr}.csv
    filename = f'{selected_database}_{table}_results_{team_abbr}.csv'
    
    # Create response
    from flask import Response
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response
