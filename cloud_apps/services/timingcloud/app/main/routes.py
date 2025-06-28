from datetime import datetime, timezone
import os
from flask import render_template, flash, redirect, send_from_directory, url_for, request, g, current_app, jsonify
from flask_babel import _, get_locale
import sqlalchemy as sa
from app import db
from app.models import RunOrder, TopLaps, CarReg, PointsLeaderboardIC, PointsLeaderboardEV, ConesLeaderboard
from app.main import bp




@bp.route('/', methods=['GET', 'POST'])
@bp.route('/runtable', methods=['GET', 'POST'])
def runtable():
    # Join RunOrder and CarReg to get team_name for each run
    query = sa.select(RunOrder, CarReg.team_name).join(CarReg, RunOrder.car_number == CarReg.car_number, isouter=True).order_by(-RunOrder.id)
    results = db.session.execute(query).all()
    # Compose car_number with team_name in the same field
    runs = []
    for run, team_name in results:
        run_display = run
        run_display.car_number = run.car_number + (f" – {team_name}" if team_name else "")
        runs.append(run_display)
    page = request.args.get('page', 1, type=int)
    return render_template('runtable.html', title='Autocross', runs=runs)

@bp.route('/api/runs', methods=['GET'])
def get_runs():
    since = request.args.get('since')
    lastrun = request.args.get('lastrun')
    if since and lastrun:
        try:
            since_timestamp = datetime.fromisoformat(since)
            try:
                int(lastrun)
                query = sa.select(RunOrder, CarReg.team_name).join(CarReg, RunOrder.car_number == CarReg.car_number, isouter=True).where(
                    sa.or_(RunOrder.updated_at > since_timestamp, RunOrder.id > lastrun)
                ).order_by(RunOrder.id)
            except:
                query = sa.select(RunOrder, CarReg.team_name).join(CarReg, RunOrder.car_number == CarReg.car_number, isouter=True).order_by(-RunOrder.id)
        except:
            query = sa.select(RunOrder, CarReg.team_name).join(CarReg, RunOrder.car_number == CarReg.car_number, isouter=True).order_by(-RunOrder.id)
    else:
        query = sa.select(RunOrder, CarReg.team_name).join(CarReg, RunOrder.car_number == CarReg.car_number, isouter=True).order_by(-RunOrder.id)

    results = db.session.execute(query).all()
    runs_data = [
        {
            'id': run.id,
            'car_number': run.car_number + (f" – {team_name}" if team_name else ""),
            'cones': run.cones,
            'off_course': run.off_course,
            'dnf': run.dnf,
            'raw_time': run.raw_time,
            'adjusted_time': run.adjusted_time
        }
        for run, team_name in results
    ]
    return jsonify(runs_data)

@bp.route('/api/runs/<int:run_id>', methods=['GET'])
def get_run(run_id):
    run = db.session.query(RunOrder).filter_by(id=run_id).first()
    if run is None:
        return jsonify({'error': 'Run not found'}), 404

    run_data = {
        'id': run.id,
        'car_number': run.car_number,
        'cones': run.cones,
        'off_course': run.off_course,
        'dnf': run.dnf,
        'raw_time': run.raw_time,
        'adjusted_time': run.adjusted_time
    }
    return jsonify(run_data)
@bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(bp.root_path, 'static'),'favicon.ico', mimetype='image/vnd.microsoft.icon')

@bp.route('/toplaps', methods=['GET', 'POST'])
def toplaps():
    query = sa.select(TopLaps)
    toplaps_data = db.session.scalars(query).all()
    runs = []
    for lap in toplaps_data:
        run = {
            'team_name': lap.team_name,
            'car_number': lap.car_number,
            'adjusted_time': lap.adjusted_time,
            'class_': lap.class_,
            'cones': lap.cones,
            'off_course': lap.off_course,
            'id': lap.id
        }
        runs.append(run)
    return render_template('toplaps.html', title='Top Laps', runs=runs)

@bp.route('/pointsLeaderboard', methods=['GET', 'POST'])
def pointsLeaderboard():
    
    query = sa.select(PointsLeaderboardIC)
    ICruns = db.session.scalars(query).all()
    query = sa.select(PointsLeaderboardEV)
    EVruns = db.session.scalars(query).all()
    
    return render_template('pointsLeaderboard.html', title='Points Leaderboard', ICruns=ICruns, EVruns=EVruns)

@bp.route('/conesLeaderboard', methods=['GET', 'POST'])
def conesLeaderboard():
        
        query = sa.select(ConesLeaderboard)
        runs = db.session.scalars(query).all()
        page = request.args.get('page', 1, type=int)
        
        return render_template('conesLeaderboard.html', title='Cones Leaderboard', runs=runs)

@bp.route('/api/points_leaderboard', methods=['GET'])
def api_points_leaderboard():
    query = sa.select(PointsLeaderboardIC)
    ICruns = db.session.scalars(query).all()
    query = sa.select(PointsLeaderboardEV)
    EVRuns = db.session.scalars(query).all()
    ic_runs_data = [
        {
            'team_name': run.team_name,
            'car_number': run.car_number,
            'adjusted_time': run.adjusted_time,
            'points': run.points
        }
        for run in ICruns
    ]
    
    ev_runs_data = [
        {
            'team_name': run.team_name,
            'car_number': run.car_number,
            'adjusted_time': run.adjusted_time,
            'points': run.points
        }
        for run in EVRuns
    ]
    
    runs_data = {
        'IC_runs': ic_runs_data,
        'EV_runs': ev_runs_data
    }
    return jsonify(runs_data)

@bp.route('/api/cones_leaderboard', methods=['GET'])
def api_cones_leaderboard():
    query = sa.select(ConesLeaderboard)
    runs = db.session.scalars(query).all()
    runs_data = [
        {
            'team_name': run.team_name,
            'car_number': run.car_number,
            'cones': run.total_cones
        }
        for run in runs
    ]
    return jsonify(runs_data)
#should top laps be limited to a certain number of laps?
@bp.route('/api/toplaps', methods=['GET'])
def api_toplaps():
    query = sa.select(TopLaps)
    toplaps_data = db.session.scalars(query).all()
    runs = []
    for lap in toplaps_data:
        run = {
            'team_name': lap.team_name,
            'car_number': lap.car_number,
            'adjusted_time': lap.adjusted_time,
            'class_': lap.class_,
            'cones': lap.cones,
            'off_course': lap.off_course,
            'id': lap.id
        }
        runs.append(run)
    return jsonify(runs)

@bp.route('/carreg', methods=['GET'])
def carreg():
    query = sa.select(CarReg)
    cars = db.session.scalars(query).all()
    return render_template('carreg.html', title='Car Registration', cars=cars)

# @bp.route('/fixdata', methods=['GET', 'POST']) #this is a temporary function to fill in adjusted times and fix data for runs that were missing them
# def fixdata():
#     query = sa.select(RunOrder)
#     runs = db.session.scalars(query).all()
#     for run in runs:
#         run = calculateAdjustedTime(run)  
#         db.session.commit()

#     return redirect(url_for('main.runtable'))
