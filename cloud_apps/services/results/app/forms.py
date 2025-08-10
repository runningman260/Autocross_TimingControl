from flask_wtf import FlaskForm
from wtforms import SelectField
from wtforms.validators import DataRequired

class DatabaseSelectForm(FlaskForm):
    database = SelectField('Select Database', validators=[DataRequired()], choices=[])