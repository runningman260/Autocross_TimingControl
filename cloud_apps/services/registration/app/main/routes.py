from datetime import datetime, timezone
import os
from flask import  request, jsonify, render_template, redirect, url_for, flash, session
from flask_babel import _
import sqlalchemy as sa
from app import db
from app.models import RunOrder, CarReg, Team
from app.main import bp
from app.main.forms import CarRegistrationForm
from sqlalchemy.exc import IntegrityError

MASTER_PASSWORD = os.environ.get("REGISTRATION_MASTER_PASSWORD", "changeme")

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == MASTER_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('main.register_car'))
        else:
            flash('Incorrect password', 'danger')
    return render_template('login.html')

@bp.route('/')
@bp.route('/register_car', methods=['GET', 'POST'])
def register_car():
    if not session.get('authenticated'):
        return redirect(url_for('main.login'))
    form = CarRegistrationForm()
    teams = db.session.query(Team).order_by(Team.name).all()
    form.team_id.choices = [(-1, "Please select")] + [(team.id, f"{team.name} ({team.abbreviation})") for team in teams]
    form.team_id.default = -1
    form.process(request.form)

    if form.validate_on_submit():
        car = CarReg(
            car_number=form.car_number.data,
            tag_number=form.tag_number.data,
            team_id=form.team_id.data,
            class_=form.class_.data,
            year=form.year.data,
            scan_time=datetime.utcnow()
        )
        db.session.add(car)
        try:
            db.session.commit()
            team = db.session.query(Team).filter_by(id=form.team_id.data).first()
            flash(f'Car {car.car_number} for team {team.name} registered successfully!', 'success')
        except IntegrityError as e:
            db.session.rollback()
            flash(f'Error: Car number {car.car_number} is already registered. Please choose a different number.', 'danger')
        return redirect(url_for('main.register_car'))
    return render_template('register_car.html', form=form)

def car_sort_key(car):
    # Accepts either a model object or a dict
    car_number = getattr(car, 'car_number', None)
    if car_number is None and isinstance(car, dict):
        car_number = car.get('car_number')
    try:
        return (0, int(car_number))
    except (ValueError, TypeError):
        return (1, str(car_number))

#carreg is now a bad name for this in retrospect, but leaving because it matches the other apps
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





##Old stuff used for car_reg_filler test script, not necessarily handled in this API but useful so leaving in.
######################################################################################################
######################################################################################################
######################################################################################################

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



