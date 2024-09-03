import sqlalchemy as sa
import sqlalchemy.orm as so
from app import create_app, db
from app.models import RunOrder, TopLaps, CarReg, PointsLeaderboard

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'RunOrder': RunOrder, 'TopLaps' : TopLaps, 'CarReg': CarReg, 'PointsLeaderboard': PointsLeaderboard}
