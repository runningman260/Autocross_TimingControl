from datetime import datetime, timezone
import os
from flask import  request, jsonify
from flask_babel import _
import sqlalchemy as sa
from app import db
from app.models import RunOrder, CarReg
from app.main import bp

@bp.before_request
def authenticate():
    auth_header = request.headers.get('Authorization')
    if auth_header != 'P59d46bV5Xy40TblyzZR6J4dz4TlJ12lIswu2iiDYw2Hr8RqtPHoAWyWC8aevdDwVLJUsurbOo4M2aSSOFmmJ5DgaItek34yHYGTAyosU7GIBYhKBuihv3GyDPlCcr6fiKk7J3w0JE1yQeqbP2UPhjfyq63Azjd1wKK8Uhl3CUqJ4BPjipvzA1W1rQXFW1xc9Qdjqcs9IwrQ3edfPXSivYL':
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
            run.updated_at = datetime.fromisoformat(run_data['updated_at'])
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
            # Update existing row
            car.scan_time = datetime.fromisoformat(car_data.get('scan_time', car.scan_time.isoformat()))
            car.tag_number = car_data.get('tag_number', car.tag_number)
            car.car_number = car_data.get('car_number', car.car_number)
            car.team_name = car_data.get('team_name', car.team_name)
            car.class_ = car_data.get('class_', car.class_)
        else:
            # Insert new row
            new_car = CarReg(**car_data)
            db.session.add(new_car)

    db.session.commit()
    return jsonify({'status': 'success'}), 200

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

