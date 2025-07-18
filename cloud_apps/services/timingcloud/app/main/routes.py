from datetime import datetime, timezone
import os
from flask import render_template, flash, redirect, send_from_directory, url_for, request, g, current_app, jsonify
from flask_babel import _, get_locale
import sqlalchemy as sa
from app import db
from app.models import RunOrder, TopLaps, CarReg, PointsLeaderboardIC, PointsLeaderboardEV, ConesLeaderboard, Team
from app.main import bp


def car_sort_key(car):
    # Accepts either a model object or a dict
    car_number = getattr(car, 'car_number', None)
    if car_number is None and isinstance(car, dict):
        car_number = car.get('car_number')
    try:
        return (0, int(car_number))
    except (ValueError, TypeError):
        return (1, str(car_number))

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/runtable', methods=['GET', 'POST'])
def runtable():
    # Join RunOrder, CarReg, and Team to get team name and abbreviation for each run
    query = (
        sa.select(RunOrder, Team.name, Team.abbreviation)
        .join(CarReg, RunOrder.car_number == CarReg.car_number, isouter=True)
        .join(Team, CarReg.team_id == Team.id, isouter=True)
        .order_by(-RunOrder.id)
    )
    results = db.session.execute(query).all()
    runs = []
    for run, team_name, team_abbr in results:
        # Attach team_name and team_abbreviation as attributes for template use
        setattr(run, 'team_name', team_name)
        setattr(run, 'team_abbreviation', team_abbr)
        runs.append(run)
    #page = request.args.get('page', 1, type=int)
    # In your runtable() route
    max_run_id = max((run.id for run in runs), default=0)
    return render_template('runtable.html', title='Autocross', runs=runs, max_run_id=max_run_id)

@bp.route('/api/runs', methods=['GET'])
def get_runs():
    since = request.args.get('since')
    lastrun = request.args.get('lastrun')
    if since and lastrun:
        try:
            since_timestamp = datetime.fromisoformat(since)
            try:
                int(lastrun)
                query = (
                    sa.select(RunOrder, Team.name, Team.abbreviation)
                    .join(CarReg, RunOrder.car_number == CarReg.car_number, isouter=True)
                    .join(Team, CarReg.team_id == Team.id, isouter=True)
                    .where(sa.or_(RunOrder.updated_at > since_timestamp, RunOrder.id > lastrun))
                    .order_by(RunOrder.id)
                )
            except:
                query = (
                    sa.select(RunOrder, Team.name, Team.abbreviation)
                    .join(CarReg, RunOrder.car_number == CarReg.car_number, isouter=True)
                    .join(Team, CarReg.team_id == Team.id, isouter=True)
                    .order_by(-RunOrder.id)
                )
        except:
            query = (
                sa.select(RunOrder, Team.name, Team.abbreviation)
                .join(CarReg, RunOrder.car_number == CarReg.car_number, isouter=True)
                .join(Team, CarReg.team_id == Team.id, isouter=True)
                .order_by(-RunOrder.id)
            )
    else:
        query = (
            sa.select(RunOrder, Team.name, Team.abbreviation)
            .join(CarReg, RunOrder.car_number == CarReg.car_number, isouter=True)
            .join(Team, CarReg.team_id == Team.id, isouter=True)
            .order_by(-RunOrder.id)
        )

    results = db.session.execute(query).all()
    runs_data = [
        {
            'id': run.id,
            'car_number': run.car_number,
            'team_name': team_name,
            'team_abbreviation': team_abbr,
            'cones': run.cones,
            'off_course': run.off_course,
            'dnf': run.dnf,
            'raw_time': run.raw_time,
            'adjusted_time': run.adjusted_time
        }
        for run, team_name, team_abbr in results
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
        for run in EVruns
    ]

    # Calculate tmax for IC and EV
    ic_times = [float(run.adjusted_time) for run in ICruns if run.adjusted_time is not None and str(run.adjusted_time).replace('.', '', 1).isdigit()]
    IC_tmax = round(1.450 * min(ic_times), 4) if ic_times else None

    ev_times = [float(run.adjusted_time) for run in EVruns if run.adjusted_time is not None and str(run.adjusted_time).replace('.', '', 1).isdigit()]
    EV_tmax = round(1.450 * min(ev_times), 4) if ev_times else None

    if request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
        runs_data = {
            'IC_runs': ic_runs_data,
            'EV_runs': ev_runs_data,
            'IC_tmax': IC_tmax,
            'EV_tmax': EV_tmax
        }
        return jsonify(runs_data)
    else:
        return render_template('pointsLeaderboard.html', title='Points Leaderboard', ICruns=ICruns, EVruns=EVruns, IC_tmax=IC_tmax, EV_tmax=EV_tmax)

@bp.route('/conesLeaderboard', methods=['GET', 'POST'])
def conesLeaderboard():
        
        query = sa.select(ConesLeaderboard)
        runs = db.session.scalars(query).all()
        page = request.args.get('page', 1, type=int)
        
        return render_template('conesLeaderboard.html', title='Cones Leaderboard', runs=runs)

# @bp.route('/api/points_leaderboard', methods=['GET'])
# def api_points_leaderboard():
#     query = sa.select(PointsLeaderboardIC)
#     ICruns = db.session.scalars(query).all()
#     query = sa.select(PointsLeaderboardEV)
#     EVRuns = db.session.scalars(query).all()
#     ic_runs_data = [
#         {
#             'team_name': run.team_name,
#             'car_number': run.car_number,
#             'adjusted_time': run.adjusted_time,
#             'points': run.points
#         }
#         for run in ICruns
#     ]
#     ev_runs_data = [
#         {
#             'team_name': run.team_name,
#             'car_number': run.car_number,
#             'adjusted_time': run.adjusted_time,
#             'points': run.points
#         }
#         for run in EVRuns
#     ]

#     # Calculate tmax for IC and EV
#     ic_times = [float(run.adjusted_time) for run in ICruns if run.adjusted_time is not None and str(run.adjusted_time).replace('.', '', 1).isdigit()]
#     IC_tmax = round(1.45 * min(ic_times), 3) if ic_times else None

#     ev_times = [float(run.adjusted_time) for run in EVRuns if run.adjusted_time is not None and str(run.adjusted_time).replace('.', '', 1).isdigit()]
#     EV_tmax = round(1.45 * min(ev_times), 3) if ev_times else None

#     runs_data = {
#         'IC_runs': ic_runs_data,
#         'EV_runs': ev_runs_data,
#         'IC_tmax': IC_tmax,
#         'EV_tmax': EV_tmax
#     }
#     return jsonify(runs_data)

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
    query = (
        sa.select(CarReg, Team.name, Team.abbreviation)
        .join(Team, CarReg.team_id == Team.id, isouter=True))
    
    results = db.session.execute(query).all()
    results = sorted(results, key=lambda row: car_sort_key(row[0]))
    cars = []
    for car, team_name, team_abbr in results:
        car_display = {
            'id': car.id,
            'scan_time': car.scan_time,
            'tag_number': car.tag_number,
            'car_number': car.car_number,
            'team_id': car.team_id,
            'team_name': team_name,
            'team_abbreviation': team_abbr,
            'class_': car.class_,
            'year': car.year
        }
        cars.append(car_display)
    # Return JSON if requested, otherwise render template
    if request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
        return jsonify(cars)
    return render_template('carreg.html', title='Car Registration', cars=cars)

# @bp.route('/fixdata', methods=['GET', 'POST']) #this is a temporary function to fill in adjusted times and fix data for runs that were missing them
# def fixdata():
#     query = sa.select(RunOrder)
#     runs = db.session.scalars(query).all()
#     for run in runs:
#         run = calculateAdjustedTime(run)  
#         db.session.commit()

#     return redirect(url_for('main.runtable'))
