from flask import request
from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, SubmitField, TextAreaField, BooleanField, SelectField
from wtforms.validators import ValidationError, DataRequired, Length
import sqlalchemy as sa
from flask_babel import _, lazy_gettext as _l
from app import db
from app.models import CarReg

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')

def car_sort_key(car):
    try:
        return (0, int(car.car_number))
    except (ValueError, TypeError):
        return (1, str(car.car_number))

class PostForm(FlaskForm):
    post = TextAreaField(_l('Say something'), validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField(_l('Submit'))

class SearchForm(FlaskForm):
    q = StringField(_l('Search'), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'meta' not in kwargs:
            kwargs['meta'] = {'csrf': False}
        super(SearchForm, self).__init__(*args, **kwargs)


class MessageForm(FlaskForm):
    message = TextAreaField(_l('Message'), validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField(_l('Submit'))

class RunEditForm(FlaskForm):
    submit_plus_cone = SubmitField(_l('+1\nCone'))
    submit_minus_cone = SubmitField(_l('-1\nCone'))
    submit_plus_oc = SubmitField(_l('+1\nOff Course'))
    submit_minus_oc = SubmitField(_l('-1\nOff Course'))
    submit_plus_dnf = SubmitField(_l('-1\nDNF'))
    submit_minus_dnf = SubmitField(_l('-1\nDNF'))
    
class AddRunForm(FlaskForm):
    car_number = SelectField(_l('Car Number'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))

    def __init__(self, *args, **kwargs):
        super(AddRunForm, self).__init__(*args, **kwargs)
        cars = db.session.query(CarReg).all()
        sorted_cars = sorted(cars, key=car_sort_key)
        self.car_number.choices = [
            ('', '-- Select Car Number --')
        ] + [
            (
                car.car_number,
                f"{car.car_number} - {car.team.name if car.team else ''} ({car.team.abbreviation if car.team else ''}) - {car.class_}"
            )
            for car in sorted_cars
        ]

class EditRunForm(FlaskForm):
    raw_time = StringField(_l('Raw Time'), validators=[DataRequired()])
    run_id = HiddenField(_l('Run ID'), validators=[DataRequired()])
    car_number = SelectField(_l('Car Number'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))

    def __init__(self, *args, **kwargs):
        super(EditRunForm, self).__init__(*args, **kwargs)
        cars = db.session.query(CarReg).all()
        sorted_cars = sorted(cars, key=car_sort_key)
        self.car_number.choices = [
            ('', '-- Select Car Number --')
        ] + [
            (
                car.car_number,
                f"{car.car_number} - {car.team.name if car.team else ''} ({car.team.abbreviation if car.team else ''}) - {car.class_}"
            )
            for car in sorted_cars
        ]

