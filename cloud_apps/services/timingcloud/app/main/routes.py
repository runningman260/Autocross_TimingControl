from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import os
from flask import render_template, flash, redirect, send_from_directory, url_for, request, g, current_app, jsonify
from flask_babel import _, get_locale
import sqlalchemy as sa
from app import db
from app.models import RunOrder, CarReg, PointsLeaderboardIC, PointsLeaderboardEV, ConesLeaderboard, Team, Accel_RunOrder, Skidpad_RunOrder, Accel_TopLaps, Skidpad_TopLaps, Accel_PointsLeaderboardIC, Accel_PointsLeaderboardEV, Skidpad_PointsLeaderboardIC, Skidpad_PointsLeaderboardEV, Autocross_TopLaps, Autocross_PointsLeaderboardIC, Autocross_PointsLeaderboardEV, Overall_PointsLeaderboardIC, Overall_PointsLeaderboardEV
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



@bp.route('/conesLeaderboard', methods=['GET', 'POST'])
def conesLeaderboard():
        
        query = sa.select(ConesLeaderboard)
        runs = db.session.scalars(query).all()
        page = request.args.get('page', 1, type=int)
        
        return render_template('conesLeaderboard.html', title='Cones Leaderboard', runs=runs)


@bp.route('/api/cones_leaderboard', methods=['GET'])
def api_cones_leaderboard():
    query = sa.select(ConesLeaderboard)
    runs = db.session.scalars(query).all()
    runs_data = [
        {
            'team_name': run.team_name,
            'car_number': run.car_number,
            'autocross_cones': run.autocross_cones,
            'accel_cones': run.accel_cones,
            'skidpad_cones': run.skidpad_cones,
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
    return render_template('carreg.html', title='Registered Cars', cars=cars)

@bp.route('/accel_runtable', methods=['GET', 'POST'])
def accel_runtable():
    query = (
        sa.select(Accel_RunOrder, Team.name, Team.abbreviation)
        .join(CarReg, Accel_RunOrder.car_number == CarReg.car_number, isouter=True)
        .join(Team, CarReg.team_id == Team.id, isouter=True)
        .order_by(-Accel_RunOrder.id)
    )
    results = db.session.execute(query).all()
    runs = []
    for run, team_name, team_abbr in results:
        setattr(run, 'team_name', team_name)
        setattr(run, 'team_abbreviation', team_abbr)
        runs.append(run)
    return render_template('accel_runtable.html', title='Acceleration Run Order', runs=runs)

@bp.route('/skidpad_runtable', methods=['GET', 'POST'])
def skidpad_runtable():
    query = (
        sa.select(Skidpad_RunOrder, Team.name, Team.abbreviation)
        .join(CarReg, Skidpad_RunOrder.car_number == CarReg.car_number, isouter=True)
        .join(Team, CarReg.team_id == Team.id, isouter=True)
        .order_by(-Skidpad_RunOrder.id)
    )
    results = db.session.execute(query).all()
    runs = []
    for run, team_name, team_abbr in results:
        setattr(run, 'team_name', team_name)
        setattr(run, 'team_abbreviation', team_abbr)
        runs.append(run)
    return render_template('skidpad_runtable.html', title='Skidpad Run Order', runs=runs)

@bp.route('/api/accel_runtable', methods=['GET'])
def api_accel_runtable():
    query = (
        sa.select(Accel_RunOrder, Team.name, Team.abbreviation)
        .join(CarReg, Accel_RunOrder.car_number == CarReg.car_number, isouter=True)
        .join(Team, CarReg.team_id == Team.id, isouter=True)
        .order_by(-Accel_RunOrder.id)
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

@bp.route('/api/skidpad_runtable', methods=['GET'])
def api_skidpad_runtable():
    query = (
        sa.select(Skidpad_RunOrder, Team.name, Team.abbreviation)
        .join(CarReg, Skidpad_RunOrder.car_number == CarReg.car_number, isouter=True)
        .join(Team, CarReg.team_id == Team.id, isouter=True)
        .order_by(-Skidpad_RunOrder.id)
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
            'raw_time_left': run.raw_time_left,
            'raw_time_right': run.raw_time_right,
            'adjusted_time': run.adjusted_time
        }
        for run, team_name, team_abbr in results
    ]
    return jsonify(runs_data)

@bp.route('/accel_toplaps', methods=['GET', 'POST'])
def accel_toplaps():
    query = sa.select(Accel_TopLaps)
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
            'id': lap.id,
            'team_abbreviation': lap.team_abbreviation
        }
        runs.append(run)
    return render_template('accel_toplaps.html', title='Acceleration Top Laps', runs=runs)

@bp.route('/api/accel_toplaps', methods=['GET'])
def api_accel_toplaps():
    query = sa.select(Accel_TopLaps)
    toplaps_data = db.session.scalars(query).all()
    runs = []
    for lap in toplaps_data:
        run = {
            'id': lap.id,
            'team_name': lap.team_name,
            'car_number': lap.car_number,
            'adjusted_time': lap.adjusted_time,
            'class_': lap.class_,
            'cones': lap.cones,
            'off_course': lap.off_course,
            'team_abbreviation': lap.team_abbreviation
        }
        runs.append(run)
    return jsonify(runs)

@bp.route('/skidpad_toplaps', methods=['GET', 'POST'])
def skidpad_toplaps():
    query = sa.select(Skidpad_TopLaps)
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
            'id': lap.id,
            'team_abbreviation': lap.team_abbreviation
        }
        runs.append(run)
    return render_template('skidpad_toplaps.html', title='Skidpad Top Laps', runs=runs)

@bp.route('/api/skidpad_toplaps', methods=['GET'])
def api_skidpad_toplaps():
    query = sa.select(Skidpad_TopLaps)
    toplaps_data = db.session.scalars(query).all()
    runs = []
    for lap in toplaps_data:
        run = {
            'id': lap.id,
            'team_name': lap.team_name,
            'car_number': lap.car_number,
            'adjusted_time': lap.adjusted_time,
            'class_': lap.class_,
            'cones': lap.cones,
            'off_course': lap.off_course,
            'team_abbreviation': lap.team_abbreviation
        }
        runs.append(run)
    return jsonify(runs)

@bp.route('/accel_pointsLeaderboard', methods=['GET', 'POST'])
def accel_pointsLeaderboard():
    target_timezone = ZoneInfo("America/New_York")
    # Show this page at 5:30 PM on August 1st 2025
    reveal_time = datetime(2025, 8, 1, 17, 30, 0, tzinfo=target_timezone)
    if((reveal_time-datetime.now(target_timezone)).total_seconds() > 0):
        return render_template('accel_pointsLeaderboard_placeholder.html', title='Acceleration Points Leaderboard')
    else:
        query = sa.select(Accel_PointsLeaderboardIC)
        ICruns = db.session.scalars(query).all()
        query = sa.select(Accel_PointsLeaderboardEV)
        EVruns = db.session.scalars(query).all()
        return render_template('accel_pointsLeaderboard.html', title='Acceleration Points Leaderboard', ICruns=ICruns, EVruns=EVruns)

@bp.route('/skidpad_pointsLeaderboard', methods=['GET', 'POST'])
def skidpad_pointsLeaderboard():
    target_timezone = ZoneInfo("America/New_York")
    # Show this page at 5:30 PM on August 1st 2025
    reveal_time = datetime(2025, 8, 1, 17, 30, 0, tzinfo=target_timezone)
    if((reveal_time-datetime.now(target_timezone)).total_seconds() > 0):
        return render_template('skidpad_pointsLeaderboard_placeholder.html', title='Skidpad Points Leaderboard')
    else:
        query = sa.select(Skidpad_PointsLeaderboardIC)
        ICruns = db.session.scalars(query).all()
        query = sa.select(Skidpad_PointsLeaderboardEV)
        EVruns = db.session.scalars(query).all()
        return render_template('skidpad_pointsLeaderboard.html', title='Skidpad Points Leaderboard', ICruns=ICruns, EVruns=EVruns)

@bp.route('/api/accel_points_leaderboard', methods=['GET'])
def api_accel_points_leaderboard():
    query = sa.select(Accel_PointsLeaderboardIC)
    ICruns = db.session.scalars(query).all()
    query = sa.select(Accel_PointsLeaderboardEV)
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
    runs_data = {
        'IC_runs': ic_runs_data,
        'EV_runs': ev_runs_data
    }
    return jsonify(runs_data)

@bp.route('/api/skidpad_points_leaderboard', methods=['GET'])
def api_skidpad_points_leaderboard():
    query = sa.select(Skidpad_PointsLeaderboardIC)
    ICruns = db.session.scalars(query).all()
    query = sa.select(Skidpad_PointsLeaderboardEV)
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
    runs_data = {
        'IC_runs': ic_runs_data,
        'EV_runs': ev_runs_data
    }
    return jsonify(runs_data)

@bp.route('/autocross_toplaps', methods=['GET', 'POST'])
def autocross_toplaps():
    query = sa.select(Autocross_TopLaps)
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
            'id': lap.id,
            'team_abbreviation': lap.team_abbreviation
        }
        runs.append(run)
    return render_template('autocross_toplaps.html', title='Autocross Top Laps', runs=runs)

@bp.route('/api/autocross_toplaps', methods=['GET'])
def api_autocross_toplaps():
    query = sa.select(Autocross_TopLaps)
    toplaps_data = db.session.scalars(query).all()
    runs = []
    for lap in toplaps_data:
        run = {
            'id': lap.id,
            'team_name': lap.team_name,
            'car_number': lap.car_number,
            'adjusted_time': lap.adjusted_time,
            'class_': lap.class_,
            'cones': lap.cones,
            'off_course': lap.off_course,
            'team_abbreviation': lap.team_abbreviation
        }
        runs.append(run)
    return jsonify(runs)

@bp.route('/autocross_pointsLeaderboard', methods=['GET', 'POST'])
def autocross_pointsLeaderboard():
    target_timezone = ZoneInfo("America/New_York")
    # Show this page at 6:30 PM on August 2nd 2025
    reveal_time = datetime(2025, 8, 2, 18, 30, 0, tzinfo=target_timezone)
    if((reveal_time-datetime.now(target_timezone)).total_seconds() > 0):
        return render_template('autocross_pointsLeaderboard_placeholder.html', title='Autocross Points Leaderboard')
    else:
        query = sa.select(Autocross_PointsLeaderboardIC)
        ICruns = db.session.scalars(query).all()
        query = sa.select(Autocross_PointsLeaderboardEV)
        EVruns = db.session.scalars(query).all()
        return render_template('autocross_pointsLeaderboard.html', title='Autocross Points Leaderboard', ICruns=ICruns, EVruns=EVruns)

@bp.route('/api/autocross_points_leaderboard', methods=['GET'])
def api_autocross_points_leaderboard():
    query = sa.select(Autocross_PointsLeaderboardIC)
    ICruns = db.session.scalars(query).all()
    query = sa.select(Autocross_PointsLeaderboardEV)
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
    runs_data = {
        'IC_runs': ic_runs_data,
        'EV_runs': ev_runs_data
    }
    return jsonify(runs_data)

@bp.route('/overall_pointsLeaderboard', methods=['GET', 'POST'])
def overall_pointsLeaderboard():
    target_timezone = ZoneInfo("America/New_York")
    # Show this page at 6:30 PM on August 2nd 2025
    reveal_time = datetime(2025, 8, 2, 18, 30, 0, tzinfo=target_timezone)
    if((reveal_time-datetime.now(target_timezone)).total_seconds() > 0):
        return render_template('overall_pointsLeaderboard_placeholder.html', title='Overall Points Leaderboard')
    else:
        query = sa.select(Overall_PointsLeaderboardIC)
        ICruns = db.session.scalars(query).all()
        query = sa.select(Overall_PointsLeaderboardEV)
        EVruns = db.session.scalars(query).all()
        return render_template('overall_pointsLeaderboard.html', title='Overall Points Leaderboard', ICruns=ICruns, EVruns=EVruns)

@bp.route('/api/overall_pointsLeaderboard', methods=['GET'])
def api_overall_pointsLeaderboard():
    query = sa.select(Overall_PointsLeaderboardIC)
    ICruns = db.session.scalars(query).all()
    query = sa.select(Overall_PointsLeaderboardEV)
    EVruns = db.session.scalars(query).all()
    IC_points_totals_data = [
        {
            'team_name': team.team_name,
            'car_number': team.car_number,
            'autocross_points' : team.autocross_points,
            'accel_points': team.accel_points,
            'skidpad_points': team.skidpad_points,
            'total_points': team.total_points
        }
        for team in ICruns
    ]
    EV_points_totals_data = [
        {
            'team_name': team.team_name,
            'car_number': team.car_number,
            'autocross_points' : team.autocross_points,
            'accel_points': team.accel_points,
            'skidpad_points': team.skidpad_points,
            'total_points': team.total_points
        }
        for team in EVruns
    ]
    points_totals_data = {
        'IC_points_totals': IC_points_totals_data,
        'EV_points_totals': EV_points_totals_data
    }
    return jsonify(points_totals_data)



