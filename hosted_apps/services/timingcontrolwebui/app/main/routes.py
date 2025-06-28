from datetime import datetime, timezone
import os
from flask import render_template, flash, redirect, send_from_directory, url_for, request, g, current_app, jsonify
from flask_babel import _, get_locale
import sqlalchemy as sa
from app import db, mqtt
from app.main.forms import EmptyForm, PostForm, SearchForm, RunEditForm, AddRunForm, EditRunForm
from app.models import RunOrder, TopLaps, CarReg, PointsLeaderboardIC, PointsLeaderboardEV, ConesLeaderboard
from app.main import bp
import requests
import threading
import time
from collections import deque


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
                # if run.raw_time is None: 
                #     run.raw_time = 0.0 
                


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
    query = sa.select(RunOrder).order_by(-RunOrder.id)
    runs = db.session.scalars(query).all()
    page = request.args.get('page', 1, type=int)
    
    return render_template('runtable.html', title='Run Table', runs=runs, form=form, addRunForm=addRunForm, editRunForm=editRunForm)


# --- Sync Thread Globals ---
sync_thread = None
sync_thread_running = True
sync_thread_paused = True
sync_log = deque(maxlen=100)  # use deque for thread-safe rolling log
sync_log_lock = threading.Lock()

def append_sync_log(line):
    with sync_log_lock:
        sync_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {line}")

def log_no_runs_to_sync():
    with sync_log_lock:
        msg = "No runs to sync."
        if sync_log and sync_log[-1].endswith(msg):
            sync_log.pop()
        sync_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def sync_with_cloud_loop(app):
    global sync_thread_running, sync_thread_paused
    with app.app_context():
        append_sync_log("Sync thread Paused.")
        while sync_thread_running:
            if sync_thread_paused:
                time.sleep(1)
                continue
            try:
                #append_sync_log("Sync cycle started.")
                # Query rows that need to be synced
                query = sa.select(RunOrder).where(
                    sa.or_(
                        RunOrder.updated_at > RunOrder.last_synced_at,
                        RunOrder.last_synced_at.is_(None)
                    )
                ).order_by(RunOrder.updated_at)
                runs_to_sync = db.session.scalars(query).all()
                #append_sync_log(f"Found {len(runs_to_sync)} runs to sync.")
                batch_size = 50
                batches = [runs_to_sync[i:i + batch_size] for i in range(0, len(runs_to_sync), batch_size)]

                if not runs_to_sync:
                    log_no_runs_to_sync()
                    time.sleep(5)
                    continue  # No runs to sync, skip to next cycle

                for batch in batches:
                    runs_data = [
                        {
                            'id': run.id,
                            'car_number': run.car_number,
                            'cones': run.cones,
                            'off_course': run.off_course,
                            'dnf': run.dnf,
                            'raw_time': run.raw_time,
                            'adjusted_time': run.adjusted_time,
                            'updated_at': run.updated_at.isoformat()
                        }
                        for run in batch
                    ]
                    append_sync_log(f"Syncing batch with {len(runs_data)} runs: " +
                        ", ".join([f"ID {r['id']} (Car {r['car_number']})" for r in runs_data]))
                    try:
                        response = requests.post(
                            'https://trackapi.guttenp.land/api/update_runs',
                            json={'runs': runs_data},
                            headers={'Authorization': 'P59d46bV5Xy40TblyzZR6J4dz4TlJ12lIswu2iiDYw2Hr8RqtPHoAWyWC8aevdDwVLJUsurbOo4M2aSSOFmmJ5DgaItek34yHYGTAyosU7GIBYhKBuihv3GyDPlCcr6fiKk7J3w0JE1yQeqbP2UPhjfyq63Azjd1wKK8Uhl3CUqJ4BPjipvzA1W1rQXFW1xc9Qdjqcs9IwrQ3edfPXSivYL'}
                        )
                        if response.status_code == 200:
                            for run in batch:
                                run.last_synced_at = datetime.now(timezone.utc)
                                append_sync_log(f"Run {run.id} (Car {run.car_number}) marked as synced at {run.last_synced_at.isoformat()}")
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
                    'adjusted_time': new_run.adjusted_time
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

@bp.route('/edit_run/<int:run_id>', methods=['POST'])
def edit_run(run_id):
    form = EditRunForm()
    if form.validate_on_submit():
        run = db.session.query(RunOrder).filter_by(id=run_id).first()
        if run:
            oldtime = run.raw_time
            run.raw_time = form.raw_time.data
            db.session.commit()
            #flash(_('Run '+ str(run.id) + ' car #'+run.car_number+' updated successfully from '+ str(oldtime) + ' to ' + str(run.raw_time)))
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
                    'adjusted_time': run.adjusted_time
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
    #fixdata()
    since = request.args.get('since')
    lastrun = request.args.get('lastrun')
    if since and lastrun:
        try:
            since_timestamp = datetime.fromisoformat(since)
            try:
                int(lastrun)
                query = sa.select(RunOrder).where(sa.or_(RunOrder.updated_at > since_timestamp,RunOrder.id > lastrun)).order_by(RunOrder.id)
            except:
                query = sa.select(RunOrder).order_by(-RunOrder.id)
        except:
            query = sa.select(RunOrder).order_by(-RunOrder.id)        
    else:
        query = sa.select(RunOrder).order_by(-RunOrder.id)
    
    
    runs=db.session.scalars(query).all()
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
        for run in runs
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

