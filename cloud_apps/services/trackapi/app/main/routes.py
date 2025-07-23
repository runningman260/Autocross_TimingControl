from datetime import datetime, timezone
import os
from flask import  request, jsonify
from flask_babel import _
import sqlalchemy as sa
from app import db
from app.models import RunOrder, CarReg, Team, Skidpad_RunOrder, Accel_RunOrder
from app.main import bp

@bp.before_request
def authenticate():
    auth_header = request.headers.get('Authorization')
    if auth_header != 'Bearer ' + os.getenv('TRACKAPI_AUTH_TOKEN'):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    
@bp.route('/api/update_runs', methods=['POST'])
def update_runs():
    data = request.json
    if not data or 'runs' not in data:
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400

    for run_data in data['runs']:
        run = db.session.query(RunOrder).filter_by(id=run_data['id']).first()
        if run:
            # Update existing row
            run.car_number = run_data.get('car_number', run.car_number)
            run.cones = run_data.get('cones', run.cones)
            run.off_course = run_data.get('off_course', run.off_course)
            run.dnf = run_data.get('dnf', run.dnf)
            run.raw_time = run_data.get('raw_time', run.raw_time)
            run.adjusted_time = run_data.get('adjusted_time', run.adjusted_time)
        else:
            # Insert new row
            new_run = RunOrder(**run_data)
            db.session.add(new_run)

    db.session.commit()
    return jsonify({'status': 'success'}), 200

@bp.route('/api/update_car_regs', methods=['POST'])
def update_car_regs():
    data = request.json
    if not data or 'car_regs' not in data:
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400

    for car_data in data['car_regs']:
        car = db.session.query(CarReg).filter_by(id=car_data.get('id')).first()
        if car:
            scan_time_val = car_data.get('scan_time')
            if scan_time_val is not None:
                if isinstance(scan_time_val, str):
                    car.scan_time = datetime.fromisoformat(scan_time_val)
                elif isinstance(scan_time_val, datetime):
                    car.scan_time = scan_time_val
            car.tag_number = car_data.get('tag_number', car.tag_number)
            car.car_number = car_data.get('car_number', car.car_number)
            car.team_id = car_data.get('team_id', car.team_id)
            car.class_ = car_data.get('class_', car.class_)
            car.year = car_data.get('year', car.year)
        else:
            new_car = CarReg(
                scan_time=datetime.fromisoformat(car_data['scan_time']),
                tag_number=car_data['tag_number'],
                car_number=car_data['car_number'],
                team_id=car_data['team_id'],
                class_=car_data['class_'],
                year=car_data.get('year', '')
            )
            db.session.add(new_car)

    db.session.commit()
    return jsonify({'status': 'success'}), 200

from app.models import Team

@bp.route('/api/teams', methods=['GET'])
def get_teams():
    teams = db.session.query(Team).all()
    result = [
        {
            'id': team.id,
            'name': team.name,
            'abbreviation': team.abbreviation
        }
        for team in teams
    ]
    return jsonify(result)

@bp.route('/api/car_regs', methods=['GET'])
def get_car_regs():
    car_regs = db.session.query(CarReg).all()
    result = [
        {
            'id': car.id,
            'scan_time': car.scan_time.isoformat() if car.scan_time else None,
            'tag_number': car.tag_number,
            'car_number': car.car_number,
            'team_id': car.team_id,
            'class_': car.class_,
            'year': car.year
        }
        for car in car_regs
    ]
    return jsonify(result)

def safe_isoformat(dt):
    if isinstance(dt, datetime):
        return dt.isoformat()
    return dt if isinstance(dt, str) else None

@bp.route('/api/car_regs/modified_since', methods=['GET'])
def get_car_regs_modified_since():
    timestamp = request.args.get('since')
    if not timestamp:
        return jsonify({'status': 'error', 'message': 'Missing "since" query parameter'}), 400
    try:
        since_dt = datetime.fromisoformat(timestamp)
    except Exception:
        return jsonify({'status': 'error', 'message': 'Invalid timestamp format'}), 400

    car_regs = db.session.query(CarReg).filter(CarReg.updated_at > since_dt).all()
    result = [
        {
            'id': car.id,
            'scan_time': safe_isoformat(car.scan_time),
            'tag_number': car.tag_number,
            'car_number': car.car_number,
            'team_id': car.team_id,
            'class_': car.class_,
            'year': getattr(car, 'year', None),
            'created_at': safe_isoformat(getattr(car, 'created_at', None)),
            'updated_at': safe_isoformat(getattr(car, 'updated_at', None))
        }
        for car in car_regs
    ]
    return jsonify(result)

@bp.route('/api/skidpad_runs', methods=['GET'])
def get_skidpad_runs():
    runs = db.session.query(Skidpad_RunOrder).all()
    runs_data = [
        {
            'id': run.id,
            'car_number': run.car_number,
            'cones': run.cones,
            'off_course': run.off_course,
            'dnf': run.dnf,
            'raw_time_left': run.raw_time_left,
            'raw_time_right': run.raw_time_right,
            'adjusted_time': run.adjusted_time,
            'created_at': run.created_at.isoformat() if hasattr(run, 'created_at') and run.created_at else None,
            'updated_at': run.updated_at.isoformat() if hasattr(run, 'updated_at') and run.updated_at else None
        }
        for run in runs
    ]
    return jsonify(runs_data)

@bp.route('/api/accel_runs', methods=['GET'])
def get_accel_runs():
    runs = db.session.query(Accel_RunOrder).all()
    runs_data = [
        {
            'id': run.id,
            'car_number': run.car_number,
            'cones': run.cones,
            'off_course': run.off_course,
            'dnf': run.dnf,
            'raw_time': run.raw_time,
            'adjusted_time': run.adjusted_time,
            'created_at': run.created_at.isoformat() if hasattr(run, 'created_at') and run.created_at else None,
            'updated_at': run.updated_at.isoformat() if hasattr(run, 'updated_at') and run.updated_at else None
        }
        for run in runs
    ]
    return jsonify(runs_data)

# @bp.route('/api/runs', methods=['GET'])
# def get_runs():
#     #fixdata()
#     since = request.args.get('since')
#     lastrun = request.args.get('lastrun')
#     if since and lastrun:
#         try:
#             since_timestamp = datetime.fromisoformat(since)
#             try:
#                 int(lastrun)
#                 query = sa.select(RunOrder).where(sa.or_(RunOrder.updated_at > since_timestamp,RunOrder.id > lastrun)).order_by(RunOrder.id)
#             except:
#                 query = sa.select(RunOrder).order_by(-RunOrder.id)
#         except:
#             query = sa.select(RunOrder).order_by(-RunOrder.id)        
#     else:
#         query = sa.select(RunOrder).order_by(-RunOrder.id)
    
    
#     runs=db.session.scalars(query).all()
#     runs_data = [
#         {
#             'id': run.id,
#             'car_number': run.car_number,
#             'cones': run.cones,
#             'off_course': run.off_course,
#             'dnf': run.dnf,
#             'raw_time': run.raw_time,
#             'adjusted_time': run.adjusted_time
#         }
#         for run in runs
#     ]
#     return jsonify(runs_data)

# @bp.route('/api/runs/<int:run_id>', methods=['GET'])
# def get_run(run_id):
#     run = db.session.query(RunOrder).filter_by(id=run_id).first()
#     if run is None:
#         return jsonify({'error': 'Run not found'}), 404

#     run_data = {
#         'id': run.id,
#         'car_number': run.car_number,
#         'cones': run.cones,
#         'off_course': run.off_course,
#         'dnf': run.dnf,
#         'raw_time': run.raw_time,
#         'adjusted_time': run.adjusted_time
#     }
#     return jsonify(run_data)

