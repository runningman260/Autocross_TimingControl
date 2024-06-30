from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, g, \
    current_app
from flask_babel import _, get_locale
import sqlalchemy as sa
from app import db
from app.main.forms import EmptyForm, PostForm, SearchForm
from app.models import RunOrder
from app.main import bp

@bp.route('/', methods=['GET', 'POST'])
### Nick Start
@bp.route('/runtable', methods=['GET', 'POST'])
def runtable():
    query = sa.select(RunOrder)
    runs = db.session.scalars(query).all()
    inst = sa.inspect(RunOrder)
    cols = [c_attr.key for c_attr in inst.mapper.column_attrs]
    page = request.args.get('page', 1, type=int)
    
    return render_template('runtable.html', title='Run Table', runs=runs, cols=cols)
