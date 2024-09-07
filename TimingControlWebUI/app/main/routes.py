from datetime import datetime, timezone
import os
from flask import render_template, flash, redirect, send_from_directory, url_for, request, g, current_app, jsonify
from flask_babel import _, get_locale
import sqlalchemy as sa
from app import db, mqtt
from app.main.forms import EmptyForm, PostForm, SearchForm, RunEditForm, AddRunForm, EditRunForm
from app.models import RunOrder, TopLaps, CarReg, PointsLeaderboard, ConesLeaderboard
from app.main import bp

def calculateAdjustedTime(run:RunOrder):
    # I hate that this is at the top here

    if "DNF" in str(run.dnf):
        run.adjusted_time = "DNF"
    else:
        if run.adjusted_time==0.0: 
            run.adjusted_time=run.raw_time
        offset:int = 0
        #run.adjusted_time = float(run.raw_time)
        offset += int(run.cones) * 2
        offset += int(run.off_course) * 20
        offset += float(run.raw_time)
        offset = round(offset, 3)
        run.adjusted_time = offset
        #print(f"Adjusted Time: {run.adjusted_time}")
    return run


@bp.route('/', methods=['GET', 'POST'])
### Nick Start
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
                        actionmessage='Did Not Finish'
                    elif "DNF" in str(run.dnf):
                        run.dnf=None
                        actionmessage='Removed DNF'  

                
                carmessage += "Run " + f"{run.id}"+ " Car " +f"{run.car_number} - " + actionmessage + "<br>"
                #run = calculateAdjustedTime(run)
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

@bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(bp.root_path, 'static'),'favicon.ico', mimetype='image/vnd.microsoft.icon')

@bp.route('/toplaps', methods=['GET', 'POST'])
def toplaps():
    
    query = sa.select(TopLaps)
    runs = db.session.scalars(query).all()
    page = request.args.get('page', 1, type=int)
    
    return render_template('toplaps.html', title='Top Laps', runs=runs)

@bp.route('/pointsLeaderboard', methods=['GET', 'POST'])
def pointsLeaderboard():
    
    query = sa.select(PointsLeaderboard)
    runs = db.session.scalars(query).all()
    page = request.args.get('page', 1, type=int)
    
    return render_template('pointsLeaderboard.html', title='Points Leaderboard', runs=runs)

@bp.route('/conesLeaderboard', methods=['GET', 'POST'])
def conesLeaderboard():
        
        query = sa.select(ConesLeaderboard)
        runs = db.session.scalars(query).all()
        page = request.args.get('page', 1, type=int)
        
        return render_template('conesLeaderboard.html', title='Cones Leaderboard', runs=runs)

@bp.route('/fixdata', methods=['GET', 'POST']) #this is a temporary function to fill in adjusted times and fix data for runs that were missing them
def fixdata():
    query = sa.select(RunOrder)
    runs = db.session.scalars(query).all()
    for run in runs:
        run = calculateAdjustedTime(run)  
        db.session.commit()

    return redirect(url_for('main.runtable'))


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
            mqtt.publish("/timing/webui/override","A")

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
        print(run)
        if run:
            oldtime = run.raw_time
            run.raw_time = form.raw_time.data
            #run = calculateAdjustedTime(run)
            db.session.commit()
            flash(_('Run '+ str(run.id) + ' car #'+run.car_number+' updated successfully from '+ str(oldtime) + ' to ' + str(run.raw_time)))
            return redirect(url_for('main.runtable'))
    flash(_('Error updating run.'))
    return redirect(url_for('main.runtable'))

@bp.route('/api/runs', methods=['GET'])
def get_runs():
    #fixdata()#to be removed when handled by db insert of finishtime
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