from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, g, \
    current_app
from flask_babel import _, get_locale
import sqlalchemy as sa
from app import db
from app.main.forms import EmptyForm, PostForm, SearchForm, RunEditForm
from app.models import RunOrder, TopLaps
from app.main import bp

def calculateAdjustedTime(run):
    # I hate that this is at the top here
    run.adjusted_time = run.raw_time
    run.adjusted_time += run.cones
    run.adjusted_time += run.off_courses * 5
    return run


@bp.route('/', methods=['GET', 'POST'])
### Nick Start
@bp.route('/runtable', methods=['GET', 'POST'])
def runtable():
    form = RunEditForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            selected_runs = request.form.getlist('selected_runs')
            for checkbox_id in selected_runs:
                run_id=checkbox_id.split("-")
                run = db.session.query(RunOrder).filter_by(id=run_id[0], tag=run_id[1]).first()
                #why does python make me do this to load uninitialized integer fields?
                if isinstance(run.cones, str):
                    run.cones = int(0)
                if isinstance(run.off_courses, str):
                    run.off_courses = int(0)
                if run.adjusted_time==0.0: #placeholder
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
                        run.off_courses-=1  # Ensure off_courses doesn't go below 0\
                
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
    
    return render_template('runtable.html', title='Run Table', runs=runs, cols=cols, form=form)


@bp.route('/toplaps', methods=['GET', 'POST'])
def toplaps():
    
    query = sa.select(TopLaps)
    runs = db.session.scalars(query).all()
    inst = sa.inspect(TopLaps)                                 # To get headers, should probs be in the model code
    cols = [c_attr.key for c_attr in inst.mapper.column_attrs]  # To get headers, should probs be in the model code                                  # Add column header for the checkboxes
    page = request.args.get('page', 1, type=int)
    
    return render_template('toplaps.html', title='Top Laps', runs=runs, cols=cols)

@bp.route('/fixdata', methods=['GET', 'POST']) #this is a temporary function to fill in adjusted times for runs that were missing them
def fixdata():
    query = sa.select(RunOrder)
    runs = db.session.scalars(query).all()
    for run in runs:
        if run.adjusted_time == 0.0:
            run.adjusted_time = run.raw_time
        if isinstance(run.cones, str):
            run.cones = int(0)
        if isinstance(run.off_courses, str):
            run.off_courses = int(0)    
        db.session.commit()

    return redirect(url_for('main.runtable'))
