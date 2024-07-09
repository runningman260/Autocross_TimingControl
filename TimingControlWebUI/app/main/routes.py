from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, g, \
    current_app
from flask_babel import _, get_locale
import sqlalchemy as sa
from app import db
from app.main.forms import EmptyForm, PostForm, SearchForm, RunEditForm, RunSelectForm
from app.models import RunOrder
from app.main import bp

@bp.route('/', methods=['GET', 'POST'])
### Nick Start
@bp.route('/runtable', methods=['GET', 'POST'])
def runtable():
    form = RunEditForm()
    cb = RunSelectForm()
    #Need on-submit for each of the buttons
    #if form.validate_on_submit():
        # Four different "submits" that get handled independantly. 
        #submit_plus_cone
        #submit_minus_cone
        #submit_plus_oc
        #submit_minus_oc
    query = sa.select(RunOrder)
    runs = db.session.scalars(query).all()
    inst = sa.inspect(RunOrder)                                 # To get headers, should probs be in the model code
    cols = [c_attr.key for c_attr in inst.mapper.column_attrs]  # To get headers, should probs be in the model code
    cols.insert(0, "Select")                                    # Add column header for the checkboxes
    page = request.args.get('page', 1, type=int)
    
    return render_template('runtable.html', title='Run Table', runs=runs, cols=cols, form=form, cb=cb)
