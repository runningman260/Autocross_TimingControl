from datetime import datetime, timezone
import os
from flask import  request, jsonify, render_template, redirect, url_for, flash, session
from flask_babel import _
import sqlalchemy as sa
from app import db
from app.models import RunOrder, CarReg, Team, Accel_RunOrder, Skidpad_RunOrder, ConesLeaderboard, Accel_PointsLeaderboardIC, Accel_PointsLeaderboardEV, Skidpad_PointsLeaderboardIC, Skidpad_PointsLeaderboardEV, Autocross_PointsLeaderboardIC, Autocross_PointsLeaderboardEV, Overall_PointsLeaderboardIC, Overall_PointsLeaderboardEV, News
from app.main import bp
from app.main.forms import CarRegistrationForm
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
import csv
from io import StringIO

MASTER_PASSWORD = os.environ.get("REGISTRATION_MASTER_PASSWORD", "changeme")

@bp.route('/login', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next')
    if request.method == 'POST':
        password = request.form.get('password')
        if password == MASTER_PASSWORD:
            session['authenticated'] = True
            # Redirect to next_url if present, else to register_car
            return redirect(next_url or url_for('main.register_car'))
        else:
            flash('Incorrect password', 'danger')
    return render_template('login.html', next=next_url)

@bp.route('/', methods=['GET', 'POST']) #fix for form not working without explicit path specified - needs post method allowed for root path 
@bp.route('/register_car', methods=['GET', 'POST'])
def register_car():
    if not session.get('authenticated'):
        return redirect(url_for('main.login', next=request.url))
    teams = db.session.query(Team).order_by(Team.name).all()
    team_choices = [(-1, "Please select")] + [(team.id, f"{team.name} ({team.abbreviation})") for team in teams]
    form = CarRegistrationForm()
    form.team_id.choices = team_choices
    form.team_id.default = -1
    if request.method == 'POST':
        if form.validate_on_submit():
            car = CarReg(
                car_number=form.car_number.data,
                team_id=form.team_id.data,
                class_=form.class_.data,
                year=form.year.data
            )
            db.session.add(car)
            try:
                db.session.commit()
                team = db.session.query(Team).filter_by(id=form.team_id.data).first()
                flash(f'Car {car.car_number} for team {team.name} registered successfully!', 'success')
            except IntegrityError as e:
                db.session.rollback()
                print(f"IntegrityError: {e}")
                flash(f'Error: Car number {car.car_number} is already registered. Please choose a different number.', 'danger')
            return redirect(url_for('main.register_car'))
        else:
            # Handle validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'danger')
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
    if not session.get('authenticated'):
        return redirect(url_for('main.login', next=request.url))
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

@bp.route('/upload_accel', methods=['GET', 'POST'])
def upload_accel():
    if not session.get('authenticated'):
        return redirect(url_for('main.login', next=request.url))
    message = None
    if request.method == 'POST':
        csv_data = request.form.get('csv_data', '')
        file = request.files.get('csv_file')
        if file and file.filename:
            csv_text = file.read().decode('utf-8')
        else:
            csv_text = csv_data
        reader = csv.DictReader(StringIO(csv_text))
        count = 0
        for row in reader:
            # Flexible header mapping for accel
            run_number = row.get('Run Number') or row.get('run_number')
            car_number = row.get('Car Number') or row.get('car_number')
            cones = row.get('CONE Count') or row.get('cones') or 0
            off_course = row.get('OFF COURSE Count') or row.get('off_course') or 0
            # Accept both standard and user-facing headers for raw time
            raw_time = row.get('Raw Time or DNF') or row.get('raw_time')
            # No longer convert DNF to None; keep as DNF if present
            dnf = None
            # Convert cones/off_course to int or 0
            try:
                cones = int(cones) if cones not in (None, '', ' ') else 0
            except ValueError:
                cones = 0
            try:
                off_course = int(off_course) if off_course not in (None, '', ' ') else 0
            except ValueError:
                off_course = 0
            # Skip empty, calculated, or summary rows
            if not (run_number or car_number or raw_time or cones or off_course):
                continue
            if str(run_number).strip() == '' and str(car_number).strip() == '' and (raw_time is None or str(raw_time).strip() == ''):
                continue
            if 'WINNING RUN' in str(row.values()):
                continue
            # Overwrite if run with same ID exists
            existing = db.session.query(Accel_RunOrder).filter_by(id=run_number).first()
            if existing:
                existing.car_number = car_number
                existing.raw_time = raw_time
                existing.cones = cones
                existing.off_course = off_course
                existing.dnf = dnf
                existing.adjusted_time = None
            else:
                run = Accel_RunOrder(
                    id=run_number,  # If your model uses id as run number
                    car_number=car_number,
                    raw_time=raw_time,
                    cones=cones,
                    off_course=off_course,
                    dnf=dnf,  # Let DB logic handle DNF if not present
                    adjusted_time=None  # Let DB logic calculate
                )
                db.session.add(run)
            count += 1
        db.session.commit()
        message = f"{count} acceleration runs uploaded."
    return render_template('upload_event.html', event_name='Acceleration', message=message)

@bp.route('/upload_autox', methods=['GET', 'POST'])
def upload_autox():
    if not session.get('authenticated'):
        return redirect(url_for('main.login', next=request.url))
    message = None
    if request.method == 'POST':
        csv_data = request.form.get('csv_data', '')
        file = request.files.get('csv_file')
        if file and file.filename:
            csv_text = file.read().decode('utf-8')
        else:
            csv_text = csv_data
        reader = csv.DictReader(StringIO(csv_text))
        count = 0
        for row in reader:
            # Flexible header mapping for accel
            run_number = row.get('Run Number') or row.get('run_number')
            car_number = row.get('Car Number') or row.get('car_number')
            cones = row.get('CONE Count') or row.get('cones') or 0
            off_course = row.get('OFF COURSE Count') or row.get('off_course') or 0
            # Accept both standard and user-facing headers for raw time
            raw_time = row.get('Raw Time or DNF') or row.get('raw_time')
            # No longer convert DNF to None; keep as DNF if present
            dnf = None
            # Convert cones/off_course to int or 0
            try:
                cones = int(cones) if cones not in (None, '', ' ') else 0
            except ValueError:
                cones = 0
            try:
                off_course = int(off_course) if off_course not in (None, '', ' ') else 0
            except ValueError:
                off_course = 0
            # Skip empty, calculated, or summary rows
            if not (run_number or car_number or raw_time or cones or off_course):
                continue
            if str(run_number).strip() == '' and str(car_number).strip() == '' and (raw_time is None or str(raw_time).strip() == ''):
                continue
            if 'WINNING RUN' in str(row.values()):
                continue
            # Overwrite if run with same ID exists
            existing = db.session.query(RunOrder).filter_by(id=run_number).first()
            if existing:
                existing.car_number = car_number
                existing.raw_time = raw_time
                existing.cones = cones
                existing.off_course = off_course
                existing.dnf = dnf
                existing.adjusted_time = None
            else:
                run = RunOrder(
                    id=run_number,  # If your model uses id as run number
                    car_number=car_number,
                    raw_time=raw_time,
                    cones=cones,
                    off_course=off_course,
                    dnf=dnf,  # Let DB logic handle DNF if not present
                    adjusted_time=None  # Let DB logic calculate
                )
                db.session.add(run)
            count += 1
        db.session.commit()
        message = f"{count} autocross runs uploaded."
    return render_template('upload_event.html', event_name='Autocross', message=message)

@bp.route('/upload_skidpad', methods=['GET', 'POST'])
def upload_skidpad():
    if not session.get('authenticated'):
        return redirect(url_for('main.login', next=request.url))
    message = None
    if request.method == 'POST':
        csv_data = request.form.get('csv_data', '')
        file = request.files.get('csv_file')
        if file and file.filename:
            csv_text = file.read().decode('utf-8')
        else:
            csv_text = csv_data
        reader = csv.DictReader(StringIO(csv_text))
        count = 0
        for row in reader:
            run_number = row.get('Run Number') or row.get('run_number')
            car_number = row.get('Car Number') or row.get('car_number')
            raw_time_left = row.get('Raw LEFT Time or DNF') or row.get('raw_time_left')
            raw_time_right = row.get('Raw RIGHT Time or DNF') or row.get('raw_time_right')
            cones = row.get('CONE Count') or row.get('cones') or 0
            off_course = row.get('OFF COURSE Count') or row.get('off_course') or 0
            # Do not convert DNF to None; keep as DNF if present
            dnf = None
            # Convert cones/off_course to int or 0
            try:
                cones = int(cones) if cones not in (None, '', ' ') else 0
            except ValueError:
                cones = 0
            try:
                off_course = int(off_course) if off_course not in (None, '', ' ') else 0
            except ValueError:
                off_course = 0
            # Skip empty, calculated, or summary rows
            if not (run_number or car_number or raw_time_left or raw_time_right or cones or off_course):
                continue
            if str(run_number).strip() == '' and str(car_number).strip() == '' and (raw_time_left is None or str(raw_time_left).strip() == '') and (raw_time_right is None or str(raw_time_right).strip() == ''):
                continue
            if 'WINNING RUN' in str(row.values()):
                continue
            # Overwrite if run with same ID exists
            existing = db.session.query(Skidpad_RunOrder).filter_by(id=run_number).first()
            if existing:
                existing.car_number = car_number
                existing.raw_time_left = raw_time_left
                existing.raw_time_right = raw_time_right
                existing.cones = cones
                existing.off_course = off_course
                existing.dnf = dnf
                existing.adjusted_time = None
            else:
                run = Skidpad_RunOrder(
                    id=run_number,
                    car_number=car_number,
                    raw_time_left=raw_time_left,
                    raw_time_right=raw_time_right,
                    cones=cones,
                    off_course=off_course,
                    dnf=dnf,
                    adjusted_time=None
                )
                db.session.add(run)
            count += 1
        db.session.commit()
        message = f"{count} skidpad runs uploaded."
    return render_template('upload_event.html', event_name='Skidpad', message=message)

@bp.route('/delete_car/<int:car_id>', methods=['POST'])
def delete_car(car_id):
    if not session.get('authenticated'):
        return redirect(url_for('main.login', next=request.url))
    car = db.session.query(CarReg).filter_by(id=car_id).first()
    if car:
        db.session.delete(car)
        db.session.commit()
        flash(f"Car {car.car_number} deleted.", "success")
    else:
        flash("Car not found.", "danger")
    return redirect(url_for('main.register_car'))

##Leaderboard Routes
@bp.route('/conesLeaderboard', methods=['GET', 'POST'])
def conesLeaderboard():
        if not session.get('authenticated'):
            return redirect(url_for('main.login', next=request.url))
        query = sa.select(ConesLeaderboard)
        runs = db.session.scalars(query).all()
        page = request.args.get('page', 1, type=int)
        
        return render_template('conesLeaderboard.html', title='Cones Leaderboard', runs=runs)


@bp.route('/api/cones_leaderboard', methods=['GET'])
def api_cones_leaderboard():
    if not session.get('authenticated'):
        return redirect(url_for('main.login', next=request.url))
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


@bp.route('/accel_pointsLeaderboard', methods=['GET', 'POST'])
def accel_pointsLeaderboard():
    if not session.get('authenticated'):
        return redirect(url_for('main.login', next=request.url))
    query = sa.select(Accel_PointsLeaderboardIC)
    ICruns = db.session.scalars(query).all()
    query = sa.select(Accel_PointsLeaderboardEV)
    EVruns = db.session.scalars(query).all()
    return render_template('accel_pointsLeaderboard.html', title='Acceleration Points Leaderboard', ICruns=ICruns, EVruns=EVruns)

@bp.route('/skidpad_pointsLeaderboard', methods=['GET', 'POST'])
def skidpad_pointsLeaderboard():
    if not session.get('authenticated'):
        return redirect(url_for('main.login', next=request.url))
    query = sa.select(Skidpad_PointsLeaderboardIC)
    ICruns = db.session.scalars(query).all()
    query = sa.select(Skidpad_PointsLeaderboardEV)
    EVruns = db.session.scalars(query).all()
    return render_template('skidpad_pointsLeaderboard.html', title='Skidpad Points Leaderboard', ICruns=ICruns, EVruns=EVruns)

@bp.route('/api/accel_points_leaderboard', methods=['GET'])
def api_accel_points_leaderboard():
    if not session.get('authenticated'):
        return redirect(url_for('main.login', next=request.url))
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
    if not session.get('authenticated'):
        return redirect(url_for('main.login', next=request.url))
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

@bp.route('/autocross_pointsLeaderboard', methods=['GET', 'POST'])
def autocross_pointsLeaderboard():
    if not session.get('authenticated'):
        return redirect(url_for('main.login', next=request.url))
    query = sa.select(Autocross_PointsLeaderboardIC)
    ICruns = db.session.scalars(query).all()
    query = sa.select(Autocross_PointsLeaderboardEV)
    EVruns = db.session.scalars(query).all()
    return render_template('autocross_pointsLeaderboard.html', title='Autocross Points Leaderboard', ICruns=ICruns, EVruns=EVruns)

@bp.route('/api/autocross_points_leaderboard', methods=['GET'])
def api_autocross_points_leaderboard():
    if not session.get('authenticated'):
        return redirect(url_for('main.login', next=request.url))
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

@bp.route('/leaderboard', methods=['GET', 'POST'])
@bp.route('/overall_pointsLeaderboard', methods=['GET', 'POST'])
def overall_pointsLeaderboard():
    if not session.get('authenticated'):
        return redirect(url_for('main.login', next=request.url))
    query = sa.select(Overall_PointsLeaderboardIC)
    ICruns = db.session.scalars(query).all()
    query = sa.select(Overall_PointsLeaderboardEV)
    EVruns = db.session.scalars(query).all()
    return render_template('overall_pointsLeaderboard.html', title='Overall Points Leaderboard', ICruns=ICruns, EVruns=EVruns)

@bp.route('/api/overall_pointsLeaderboard', methods=['GET'])
def api_overall_pointsLeaderboard():
    if not session.get('authenticated'):
        return redirect(url_for('main.login', next=request.url))
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

@bp.route('/team_status', methods=['GET', 'POST'])
def team_status():
    if not session.get('authenticated'):
        return redirect(url_for('main.login', next=request.url))
    teams = db.session.scalars(sa.select(Team).order_by(Team.name)).all()
    selected_team_id = request.form.get('team_id') if request.method == 'POST' else None
    cars = []
    
    if selected_team_id:
        # Convert to int for database query
        selected_team_id = int(selected_team_id)
        cars = db.session.scalars(sa.select(CarReg).where(CarReg.team_id == selected_team_id)).all()
        
        # Handle checkbox updates
        if 'update_status' in request.form:
            print(f"DEBUG: Form data received: {dict(request.form)}")
            car_id = request.form.get('car_id')
            print(f"DEBUG: Car ID: {car_id}")
            if car_id:
                try:
                    car = db.session.get(CarReg, car_id)
                    if car:
                        old_values = (car.mech_tech_status, car.accm_tech_status, car.ev_active_status, 
                                    car.rain_test_status, car.brakes_test_staus, car.edgr_status)
                        
                        car.mech_tech_status = 'mech_tech' in request.form
                        car.accm_tech_status = 'accm_tech' in request.form
                        car.ev_active_status = 'ev_active' in request.form
                        car.rain_test_status = 'rain_test' in request.form
                        car.brakes_test_staus = 'brakes_test' in request.form
                        car.edgr_status = 'edgr' in request.form
                        
                        new_values = (car.mech_tech_status, car.accm_tech_status, car.ev_active_status, 
                                    car.rain_test_status, car.brakes_test_staus, car.edgr_status)
                        
                        if old_values != new_values:
                            db.session.commit()
                            flash(f'Tech status updated successfully for Car #{car.car_number}!', 'success')
                        else:
                            flash('No changes were made.', 'info')
                    else:
                        flash('Car not found!', 'danger')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error updating status: {str(e)}', 'danger')
            else:
                flash('Please select a car first.', 'danger')
            return redirect(url_for('main.team_status') + f'?team_id={selected_team_id}')
    
    # Handle GET request with team_id parameter
    if not selected_team_id and request.args.get('team_id'):
        selected_team_id = int(request.args.get('team_id'))
        cars = db.session.scalars(sa.select(CarReg).where(CarReg.team_id == selected_team_id)).all()
    
    return render_template('team_status.html', title='Team Status', teams=teams, cars=cars, selected_team_id=selected_team_id)

@bp.route('/edit_car', methods=['POST'])
def edit_car():
    if not session.get('authenticated'):
        return redirect(url_for('main.login', next=request.url))
    
    car_id = request.form.get('car_id')
    car_number = request.form.get('car_number')
    car_class = request.form.get('class')
    car_year = request.form.get('year')
    
    try:
        car = db.session.get(CarReg, car_id)
        if car:
            car.car_number = car_number
            car.class_ = car_class
            car.year = car_year
            db.session.commit()
            flash('Car updated successfully!', 'success')
        else:
            flash('Car not found!', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating car: {str(e)}', 'danger')
    
    return redirect(url_for('main.team_status') + f'?team_id={car.team_id}' if car else url_for('main.team_status'))

@bp.route('/update_rfid_tag', methods=['POST'])
def update_rfid_tag():
    if not session.get('authenticated'):
        return redirect(url_for('main.login', next=request.url))
    
    team_id = request.form.get('team_id')
    car_id = request.form.get('car_id')
    tag_number = request.form.get('tag_number')
    
    try:
        # Update specific car with the new tag number
        car = db.session.get(CarReg, car_id)
        if car:
            from datetime import datetime
            car.tag_number = tag_number
            car.scan_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.session.commit()
            flash(f'RFID tag updated successfully for Car #{car.car_number}!', 'success')
        else:
            flash('Car not found!', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating RFID tag: {str(e)}', 'danger')
    
    return redirect(url_for('main.team_status') + f'?team_id={team_id}')

@bp.route('/manage_news', methods=['GET', 'POST'])
def manage_news():
    if not session.get('authenticated'):
        return redirect(url_for('main.login', next=request.url))
    
    if request.method == 'POST':
        if 'delete_news' in request.form:
            news_id = request.form.get('news_id')
            if news_id:
                news_item = db.session.get(News, news_id)
                if news_item:
                    db.session.delete(news_item)
                    db.session.commit()
                    flash('News item deleted successfully!', 'success')
                else:
                    flash('News item not found!', 'danger')
        elif 'edit_news' in request.form:
            news_id = request.form.get('news_id')
            title = request.form.get('title', '').strip()
            text = request.form.get('text', '').strip()
            
            if not title or not text:
                flash('Both title and text are required!', 'danger')
            elif len(title) > 200:
                flash('Title must be 200 characters or less!', 'danger')
            elif len(text) > 254:
                flash('Text must be 254 characters or less!', 'danger')
            else:
                news_item = db.session.get(News, news_id)
                if news_item:
                    news_item.title = title
                    news_item.text = text
                    db.session.commit()
                    flash('News item updated successfully!', 'success')
                else:
                    flash('News item not found!', 'danger')
        else:
            title = request.form.get('title', '').strip()
            text = request.form.get('text', '').strip()
            
            if not title or not text:
                flash('Both title and text are required!', 'danger')
            elif len(title) > 200:
                flash('Title must be 200 characters or less!', 'danger')
            elif len(text) > 254:
                flash('Text must be 254 characters or less!', 'danger')
            else:
                news_item = News(title=title, text=text)
                db.session.add(news_item)
                db.session.commit()
                flash('News item created successfully!', 'success')
    
    news_items = db.session.scalars(sa.select(News).order_by(News.created_at.desc())).all()
    return render_template('manage_news.html', title='Manage News', news_items=news_items)

