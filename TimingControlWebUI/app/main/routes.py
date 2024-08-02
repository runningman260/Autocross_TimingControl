from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, g, current_app
from flask_babel import _, get_locale
import sqlalchemy as sa
from app import db
from app.main.forms import EmptyForm, PostForm, SearchForm, RunEditForm, AddRunForm
from app.models import RunOrder, TopLaps, CarReg
from app.main import bp

def calculateAdjustedTime(run):
    # I hate that this is at the top here
    run.adjusted_time = run.raw_time
    run.adjusted_time += run.cones * 2
    run.adjusted_time += run.off_courses * 10
    if run.dnfs != 0:
        run.adjusted_time = 0.0
    return run


@bp.route('/', methods=['GET', 'POST'])
### Nick Start
@bp.route('/runtable', methods=['GET', 'POST'])
def runtable():
    form = RunEditForm()
    addRunForm = AddRunForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            selected_runs = request.form.getlist('selected_runs')
            for checkbox_id in selected_runs:
                run_id=checkbox_id.split("-")
                run = db.session.query(RunOrder).filter_by(id=run_id[0], tag=run_id[1]).first()
                #make sure nulls got initialized
                if isinstance(run.cones, str) or isinstance(run.cones, type(None)):
                    run.cones = int(0)
                if isinstance(run.off_courses, str) or isinstance(run.off_courses, type(None)):
                    run.off_courses = int(0)
                if isinstance(run.dnfs, str) or isinstance(run.dnfs, type(None)):
                    run.dnfs = int(0)  
                if run.adjusted_time==0.0: 
                    run.adjusted_time=run.raw_time


                if 'submit_plus_cone' in request.form:
                    run.cones+=1 
                elif 'submit_minus_cone' in request.form:
                    if run.cones>0:
                        run.cones-=1  # Ensure cones doesn't go below 0
                elif 'submit_plus_oc' in request.form:
                    run.off_courses+=1  
                elif 'submit_minus_oc' in request.form:
                    if run.off_courses>0:
                        run.off_courses-=1  # Ensure off_courses doesn't go below 0
                elif 'submit_plus_dnf' in request.form:
                    if run.dnfs<1: #why do I use Capital N None here but lowercase n none in jinja?
                        run.dnfs+=1  
                elif 'submit_minus_dnf' in request.form:
                    if run.dnfs>-1:
                        run.dnfs-=1  
                
                run = calculateAdjustedTime(run)
                db.session.commit()
            #flash?
            #somehow return via ajax and keep current pageview/selections
    query = sa.select(RunOrder).order_by(-RunOrder.id)
    runs = db.session.scalars(query).all()
    inst = sa.inspect(RunOrder)                                 # To get headers, should probs be in the model code
    cols = [c_attr.key for c_attr in inst.mapper.column_attrs]  # To get headers, should probs be in the model code
    cols.insert(0, "Select")                                    # Add column header for the checkboxes
    page = request.args.get('page', 1, type=int)
    
    return render_template('runtable.html', title='Run Table', runs=runs, cols=cols, form=form, addRunForm=addRunForm)


@bp.route('/toplaps', methods=['GET', 'POST'])
def toplaps():
    
    query = sa.select(TopLaps)
    runs = db.session.scalars(query).all()
    inst = sa.inspect(TopLaps)                                 # To get headers, should probs be in the model code
    cols = [c_attr.key for c_attr in inst.mapper.column_attrs]  # To get headers, should probs be in the model code                                  # Add column header for the checkboxes
    page = request.args.get('page', 1, type=int)
    
    return render_template('toplaps.html', title='Top Laps', runs=runs, cols=cols)

@bp.route('/fixdata', methods=['GET', 'POST']) #this is a temporary function to fill in adjusted times and fix data for runs that were missing them
def fixdata():
    query = sa.select(RunOrder)
    runs = db.session.scalars(query).all()
    for run in runs:
        if run.adjusted_time == 0.0:
            run.adjusted_time = run.raw_time
        if isinstance(run.cones, str) or isinstance(run.cones, type(None)):
            run.cones = int(0)
        if isinstance(run.off_courses, str) or isinstance(run.off_courses, type(None)):
            run.off_courses = int(0)  
        if isinstance(run.dnfs, str) or isinstance(run.dnfs, type(None)):
            run.dnfs = int(0)  
        run = calculateAdjustedTime(run)  
        db.session.commit()

    return redirect(url_for('main.runtable'))


@bp.route('/add_run', methods=['GET', 'POST'])
def add_run():
    form = AddRunForm()
    if form.validate_on_submit():
        car_number = form.car_number.data
        # Query CarReg to get the team name for the given car number
        car = db.session.query(CarReg).filter_by(car_number=car_number).first()
        if car:
            team_name = car.team_name
            location = "go away"
            tag = car.tag
            # Add the new run to the RunOrder with the team name
            new_run = RunOrder(car_number=car_number, team_name=team_name, location=location, tag=tag, raw_time=0.0, adjusted_time=0.0)
            db.session.add(new_run)
            db.session.commit()
            flash('New run added successfully!', 'success')
        else:
            flash('Car number not found!', 'danger')
        return redirect(url_for('main.runtable'))
    return render_template('add_run.html', form=form)
