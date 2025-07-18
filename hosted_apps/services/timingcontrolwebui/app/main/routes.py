from datetime import datetime, timezone
import os
from flask import render_template, flash, redirect, send_from_directory, url_for, request, g, current_app, jsonify
from flask_babel import _, get_locale
import sqlalchemy as sa
from app import db, mqtt
from app.main.forms import EmptyForm, PostForm, SearchForm, RunEditForm, AddRunForm, EditRunForm
from app.models import RunOrder, TopLaps, CarReg, PointsLeaderboardIC, PointsLeaderboardEV, ConesLeaderboard, Team
from app.main import bp
import requests
import threading
import time
from collections import deque

eyesToggle= False
authtoken = 'Bearer '+os.getenv('TRACKAPI_AUTH_TOKEN')
trackapi_host = 'https://' + os.getenv('TRACKAPI_HOST')


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/runtable', methods=['GET', 'POST'])
def runtable():
    form = RunEditForm()
    addRunForm = AddRunForm()
    editRunForm = EditRunForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            selected_runs = request.form.getlist('selected_runs')
            updated_runs = []
            carmessage = ''
            actionmessage=''
            for checkbox_id in selected_runs:
                run_id=checkbox_id.split("-")
                run = db.session.query(RunOrder).filter_by(id=run_id[0], car_number=run_id[1]).first()
                #make sure nulls got initialized
                try:
                    run.cones = int(run.cones)
                except:
                    run.cones = 0   
                try:
                    run.off_course = int(run.off_course)
                except:
                    run.off_course = 0
                if 'submit_plus_cone' in request.form:
                    run.cones+=1
                    actionmessage='Added Cone'
                elif 'submit_minus_cone' in request.form:
                    if run.cones>0:
                        run.cones-=1  # Ensure cones doesn't go below 0
                        actionmessage='Removed Cone'
                elif 'submit_plus_oc' in request.form:
                    run.off_course+=1
                    actionmessage='Added Off Course'  
                elif 'submit_minus_oc' in request.form:
                    if run.off_course>0:
                        run.off_course-=1  # Ensure off_course doesn't go below 0
                        actionmessage='Removed Off Course'
                elif 'submit_plus_dnf' in request.form:
                    if "DNF" not in str(run.dnf):
                        run.dnf='DNF (u)'
                        run.finishline_scan_status = 'Manually DNF\'d'
                        actionmessage='Did Not Finish'
                    elif "DNF" in str(run.dnf):
                        run.dnf=None
                        actionmessage='Removed DNF'  
                carmessage += "Run " + f"{run.id}"+ " Car " +f"{run.car_number} - " + actionmessage + "<br>"
                db.session.commit()
                updated_runs.append(run)
            message = carmessage
            response = {
                'status': 'success',
                'message': message,
                'runs': [{
                    'id': run.id,
                    'car_number': run.car_number,
                    'cones': run.cones,
                    'off_course': run.off_course,
                    'dnf': run.dnf,
                    'raw_time': run.raw_time,
                    'adjusted_time': run.adjusted_time
                } for run in updated_runs]
            }
            return jsonify(response)
            #flash?
            #somehow return via ajax and keep current pageview/selections
    # Updated GET logic: join RunOrder, CarReg, Team
    query = (
        sa.select(RunOrder, Team.name, Team.abbreviation)
        .join(CarReg, RunOrder.car_number == CarReg.car_number, isouter=True)
        .join(Team, CarReg.team_id == Team.id, isouter=True)
        .order_by(-RunOrder.id)
    )
    results = db.session.execute(query).all()
    runs = []
    for run, team_name, team_abbr in results:
        run_display = run
        run_display.team_name = team_name
        run_display.team_abbreviation = team_abbr
        runs.append(run_display)
    page = request.args.get('page', 1, type=int)
    
    return render_template('runtable.html', title='Run Table', runs=runs, form=form, addRunForm=addRunForm, editRunForm=editRunForm)


# --- Sync Thread Globals ---
sync_thread = None
sync_thread_running = True
sync_thread_paused = True
sync_log = deque(maxlen=100)  # use deque for thread-safe rolling log
sync_log_lock = threading.Lock()

# --- CarReg Sync Globals ---
last_carreg_sync_time = time.time()
carreg_sync_interval = 30  # seconds

def append_sync_log(line):
    with sync_log_lock:
        sync_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {line}")

def log_no_runs_to_sync(newline):
    with sync_log_lock:
        msg = "No runs to sync."
        if sync_log and sync_log[-1].endswith(msg):
            sync_log.pop()
        if newline:
            sync_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def sync_with_cloud_loop(app):
    global sync_thread_running, sync_thread_paused
    with app.app_context():
        append_sync_log("Sync thread Paused.")
        last_checked_updated_at = None
        while sync_thread_running:
            if sync_thread_paused:
                time.sleep(1)
                continue
            try:
                # Track the latest updated_at at the start of the sync cycle
                last_checked_updated_at = db.session.query(sa.func.max(RunOrder.updated_at)).scalar()
                if not last_checked_updated_at:
                    last_checked_updated_at = datetime.now(timezone.utc)

                # Query rows that need to be synced, but only up to last_checked_updated_at
                query = sa.select(RunOrder).where(
                    sa.and_(
                        sa.or_(
                            RunOrder.updated_at > RunOrder.last_synced_at,
                            RunOrder.last_synced_at.is_(None)
                        ),
                        RunOrder.updated_at <= last_checked_updated_at
                    )
                ).order_by(RunOrder.updated_at)
                runs_to_sync = db.session.scalars(query).all()

                # Prepare batch info with orig_updated_at
                runs_to_sync_info = [
                    (run, run.updated_at)
                    for run in runs_to_sync
                ]
                batch_size = 50
                batches = [runs_to_sync_info[i:i + batch_size] for i in range(0, len(runs_to_sync_info), batch_size)]

                if not runs_to_sync_info:
                    log_no_runs_to_sync(True)
                    time.sleep(5)
                    continue
                log_no_runs_to_sync(False)
                for batch in batches:
                    runs_data = [
                        {
                            'id': run.id,
                            'car_number': run.car_number,
                            'cones': run.cones,
                            'off_course': run.off_course,
                            'dnf': run.dnf,
                            'raw_time': run.raw_time,
                            'adjusted_time': run.adjusted_time
                        }
                        for run, orig_updated_at in batch
                    ]
                    append_sync_log(f"Syncing batch with {len(runs_data)} runs: " +
                        ", ".join([f"ID {r['id']} (Car {r['car_number']})" for r in runs_data]))
                    try:
                        response = requests.post(os.path.join(trackapi_host, 'api', 'update_runs'),
                            json={'runs': runs_data},
                            headers={'Authorization': authtoken}
                        )
                        if response.status_code == 200:
                            for run, orig_updated_at in batch:
                                db.session.refresh(run)
                                if run.updated_at == orig_updated_at:
                                    run.last_synced_at = datetime.now(timezone.utc)
                                    append_sync_log(f"Run {run.id} (Car {run.car_number}) marked as synced at {run.last_synced_at.strftime('%H:%M:%S')}")
                                else:
                                    append_sync_log(f"Run {run.id} (Car {run.car_number}) was updated during sync, skipping last_synced_at update.")
                            db.session.commit()
                            append_sync_log("Batch synced successfully.")
                        else:
                            append_sync_log(f"Error syncing batch: {response.text}")
                    except requests.exceptions.RequestException as e:
                        append_sync_log(f"Network error: {e}")
                        break
                time.sleep(5)
            except Exception as e:
                append_sync_log(f"Sync thread error: {e}")
                time.sleep(25)


@bp.record_once
def on_load(state):
    # Use the app from the state
    app = state.app
    # Start the thread with the app context
    global sync_thread
    if sync_thread is None or not sync_thread.is_alive():
        sync_thread_obj = threading.Thread(target=sync_with_cloud_loop, args=(app,), daemon=True)
        sync_thread = sync_thread_obj
        sync_thread_obj.start()


@bp.route('/api/eyes_toggle', methods=['POST'])
def api_eyes_toggle():
    global eyesToggle
    eyesToggle = not eyesToggle
    topic = "/timing/webui/eyesoff" if eyesToggle else "/timing/webui/eyeson"
    payload = str(int(time.time()))
    mqtt.publish(topic, payload)
    return jsonify({
        "status": "off" if eyesToggle else "on",
        "timestamp": payload
    })

@bp.route('/api/eyes_toggle', methods=['GET'])
def api_eyes_toggle_status():
    global eyesToggle
    return jsonify({
        "status": "off" if eyesToggle else "on"
    })

@bp.route('/api/sync_log', methods=['GET'])
def api_sync_log():
    with sync_log_lock:
        log_copy = list(sync_log)[::-1]  # reverse the log so newest is first
    status = "Paused" if sync_thread_paused else "Running"
    return jsonify({
        "log": log_copy,
        "status": status
    })

@bp.route('/api/sync_toggle', methods=['POST'])
def api_sync_toggle():
    global sync_thread_paused
    sync_thread_paused = not sync_thread_paused
    status = "Paused" if sync_thread_paused else "Running"
    append_sync_log(f"Sync {status.lower()} by user.")
    return jsonify({"status": status})

@bp.route('/api/force_sync', methods=['POST'])
def api_force_sync():
    try:
        # Set last_synced_at to None for all runs so they will be re-synced
        num_updated = db.session.query(RunOrder).update({RunOrder.last_synced_at: None})
        db.session.commit()
        log_no_runs_to_sync(False)
        append_sync_log(f"Force sync triggered: {num_updated} runs marked for sync.")
        return jsonify({"status": "success", "message": f"Force sync triggered for {num_updated} runs."})
    except Exception as e:
        append_sync_log(f"Force sync error: {e}")
        return jsonify({"status": "error", "message": f"Force sync failed: {e}"}), 500

@bp.route('/add_run', methods=['POST'])
def add_run():
    form = AddRunForm()
    if form.validate_on_submit():
        car_number = form.car_number.data
        # Query CarReg to get the team name for the given car number
        car = db.session.query(CarReg).filter_by(car_number=car_number).first()
        if car:
            
            # Add the new run to the RunOrder with the team name
            new_run = RunOrder(car_number=car_number, raw_time=None, adjusted_time=0.0, cones=0, off_course=0, startline_scan_status='Manually Added at ' + datetime.now().strftime('%H:%M:%S'))
            db.session.add(new_run)
            db.session.commit()
            response = {
                'status': 'success',
                'message': 'New run added successfully!',
                'run': {
                    'id': new_run.id,
                    'car_number': new_run.car_number,
                    'cones': new_run.cones,
                    'off_course': new_run.off_course,
                    'dnf': new_run.dnf,
                    'raw_time': new_run.raw_time,
                    'adjusted_time': new_run.adjusted_time,
                    'team_name': car.team.name if car.team else None,
                    'team_abbreviation': car.team.abbreviation if car.team else None
                }
            }
            # Let the Traffic Light Controller know to unlock the red->yellow transition
            res = mqtt.publish("/timing/webui/override","A")
            if res[0] != 0:
                response['status'] = 'warning'
                response['message'] = 'Run Added - Error unlocking red->yellow transition'
            return jsonify(response), 200
        else:
            response = {
                'status': 'danger',
                'message': 'Car number not found!'
            }
            return jsonify(response), 404
    response = {
        'status': 'danger',
        'message': 'Form validation failed!'
    }
    return jsonify(response), 400

def car_sort_key(car):
    # Accepts either a model object or a dict
    car_number = getattr(car, 'car_number', None)
    if car_number is None and isinstance(car, dict):
        car_number = car.get('car_number')
    try:
        return (0, int(car_number))
    except (ValueError, TypeError):
        return (1, str(car_number))

@bp.route('/edit_run/<int:run_id>', methods=['POST'])
def edit_run(run_id):
    form = EditRunForm()
    # Always set choices before validation
    cars = db.session.query(CarReg).all()
    sorted_cars = sorted(cars, key=car_sort_key)
    form.car_number.choices = [
        ('', '-- Select Car Number --')
    ] + [
        (
            car.car_number,
            f"{car.car_number} - {car.team.name if car.team else ''} ({car.team.abbreviation if car.team else ''}) - {car.class_}"
        )
        for car in sorted_cars
    ]
    if form.validate_on_submit():
        run = db.session.query(RunOrder).filter_by(id=run_id).first()
        if run:
            oldtime = run.raw_time
            old_car_number = run.car_number
            new_car_number = form.car_number.data

            # Only update if car number changed
            car_changed = new_car_number != old_car_number
            if car_changed:
                car_reg = db.session.query(CarReg).filter_by(car_number=new_car_number).first()
                if not car_reg:
                    return jsonify({
                        'status': 'danger',
                        'message': f'Car number {new_car_number} not found in CarReg!'
                    }), 400
                run.car_number = new_car_number
            else:
                car_reg = db.session.query(CarReg).filter_by(car_number=run.car_number).first()

            run.raw_time = form.raw_time.data
            db.session.commit()

            if car_changed:
                response = {
                    'status': 'warning',
                    'message': f'Run {run.id} car changed from #{old_car_number} to #{run.car_number} and updated from {oldtime} to {run.raw_time}',
                    'run': {
                        'id': run.id,
                        'car_number': run.car_number,
                        'cones': run.cones,
                        'off_course': run.off_course,
                        'dnf': run.dnf,
                        'raw_time': run.raw_time,
                        'adjusted_time': run.adjusted_time,
                        'team_name': car_reg.team.name if car_reg and car_reg.team else None,
                        'team_abbreviation': car_reg.team.abbreviation if car_reg and car_reg.team else None
                    }
                }
            else:
                response = {
                    'status': 'success',
                    'message': f'Run {run.id} car #{run.car_number} updated successfully from {oldtime} to {run.raw_time}',
                    'run': {
                        'id': run.id,
                        'car_number': run.car_number,
                        'cones': run.cones,
                        'off_course': run.off_course,
                        'dnf': run.dnf,
                        'raw_time': run.raw_time,
                        'adjusted_time': run.adjusted_time,
                        'team_name': car_reg.team.name if car_reg and car_reg.team else None,
                        'team_abbreviation': car_reg.team.abbreviation if car_reg and car_reg.team else None
                    }
                }
            return jsonify(response), 200
    response = {
        'status': 'danger',
        'message': 'Form validation failed!'
    }
    return jsonify(response), 400

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
    query = (
        sa.select(CarReg, Team.name, Team.abbreviation)
        .join(Team, CarReg.team_id == Team.id, isouter=True)
    )
    results = db.session.execute(query).all()
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
    # Sort cars using the custom sort key
    cars = sorted(cars, key=car_sort_key)
    # Return JSON if requested, otherwise render template
    if request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']:
        return jsonify(cars)
    return render_template('carreg.html', title='Car Registration', cars=cars)

def sync_carreg_with_cloud(force=False):
    try:
        log_no_runs_to_sync(False)
        append_sync_log("Manual CarReg sync started.")
        try:
            if force:
                since = "1970-01-01T00:00:00+00:00"
            else:
                most_recent = db.session.query(CarReg).order_by(CarReg.updated_at.desc()).first()
                since = most_recent.updated_at.isoformat() if most_recent and most_recent.updated_at else "1970-01-01T00:00:00+00:00"
            url = trackapi_host+"/api/car_regs/modified_since"
            params = {"since": since}
            # Add Authorization header (same as update_runs)
            headers = {
                'Authorization': authtoken
            }
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                car_regs = response.json()
                for car in car_regs:
                    # Ensure team exists
                    team = db.session.query(Team).filter_by(id=car['team_id']).first()
                    if not team:
                        continue
                    # Upsert CarReg
                    local_car = db.session.query(CarReg).filter_by(car_number=car['car_number']).first()
                    if local_car:
                        local_car.scan_time = datetime.fromisoformat(car['scan_time']) if car['scan_time'] else None
                        local_car.tag_number = car['tag_number']
                        local_car.team_id = car['team_id']
                        local_car.class_ = car['class_']
                        local_car.year = car.get('year', '')
                        local_car.updated_at = datetime.fromisoformat(car['updated_at']) if car['updated_at'] else datetime.now(timezone.utc)
                        print(f"[CarReg Sync] Updated car_number={local_car.car_number}, team_id={local_car.team_id}")
                    else:
                        new_car = CarReg(
                            scan_time=datetime.fromisoformat(car['scan_time']) if car['scan_time'] else None,
                            tag_number=car['tag_number'],
                            car_number=car['car_number'],
                            team_id=car['team_id'],
                            class_=car['class_'],
                            year=car.get('year', ''),
                            created_at=datetime.fromisoformat(car['created_at']) if car['created_at'] else datetime.now(timezone.utc),
                            updated_at=datetime.fromisoformat(car['updated_at']) if car['updated_at'] else datetime.now(timezone.utc)
                        )
                        db.session.add(new_car)
                        print(f"[CarReg Sync] Added car_number={new_car.car_number}, team_id={new_car.team_id}")
                db.session.commit()
                append_sync_log(f"CarReg sync: {len(car_regs)} records updated from cloud.")
            else:
                append_sync_log(f"CarReg sync error: {response.text}")
        except Exception as e:
            append_sync_log(f"CarReg sync error: {e}")
        append_sync_log("Manual CarReg sync completed successfully.")
        return True, "CarReg sync completed."
    except Exception as e:
        append_sync_log(f"Manual CarReg sync failed: {e}")
        return False, f"CarReg sync failed: {e}"

@bp.route('/api/carreg_sync', methods=['POST'])
def api_carreg_sync():
    force = False
    if request.is_json:
        data = request.get_json()
        force = data.get('force', False)
    success, message = sync_carreg_with_cloud(force=force)
    return jsonify({
        "status": "success" if success else "danger",
        "message": message
    })

