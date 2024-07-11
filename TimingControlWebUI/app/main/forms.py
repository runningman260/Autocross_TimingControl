from flask import request
from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import ValidationError, DataRequired, Length
import sqlalchemy as sa
from flask_babel import _, lazy_gettext as _l
from app import db

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


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
    

class RunSelectForm(FlaskForm):
    enabled = BooleanField("") # Not sure if this is right