# app/main/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired
from datetime import datetime

class CarRegistrationForm(FlaskForm):
    car_number = StringField('Car Number', validators=[DataRequired()])
    tag_number = StringField('Tag Number', validators=[DataRequired()])
    team_id = SelectField('Team', coerce=int, validators=[DataRequired()])
    class_ = SelectField('Class', choices=[('IC', 'IC'), ('EV', 'EV'), ('MOD', 'MOD')], validators=[DataRequired()])
    currentYear = datetime.now().year
    year = IntegerField('Year', default=currentYear, render_kw={"min": 1900, "max": currentYear, "step": 1})
    submit = SubmitField('Register Car')

    def validate_team_id(self, field):
        if field.data == -1:
            raise ValueError("Please select a team.")