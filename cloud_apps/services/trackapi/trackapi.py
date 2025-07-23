import sqlalchemy as sa
import sqlalchemy.orm as so
from app import create_app, db
from app.models import RunOrder, CarReg, Team, Skidpad_RunOrder, Accel_RunOrder

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'RunOrder': RunOrder, 'CarReg': CarReg, 'Team': Team, 'Skidpad_RunOrder': Skidpad_RunOrder, 'Accel_RunOrder': Accel_RunOrder}
