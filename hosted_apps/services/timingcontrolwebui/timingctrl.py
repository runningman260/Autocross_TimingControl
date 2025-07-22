import sqlalchemy as sa
import sqlalchemy.orm as so
from app import create_app, db
from app.models import RunOrder, Accel_RunOrder, Skidpad_RunOrder, CarReg, Autocross_TopLaps, Accel_TopLaps, Skidpad_TopLaps, Autocross_PointsLeaderboardIC, Autocross_PointsLeaderboardEV, Accel_PointsLeaderboardIC, Accel_PointsLeaderboardEV, Skidpad_PointsLeaderboardIC, Skidpad_PointsLeaderboardEV, Overall_PointsLeaderboardIC, Overall_PointsLeaderboardEV, ConesLeaderboard, Team

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'sa'                            : sa, 
            'so'                            : so, 
            'db'                            : db, 
            'RunOrder'                      : RunOrder, 
            'Accel_RunOrder'                : Accel_RunOrder,
            'Skidpad_RunOrder'              : Skidpad_RunOrder, 
            'CarReg'                        : CarReg, 
            'Autocross_TopLaps'             : Autocross_TopLaps,
            'Accel_TopLaps'                 : Accel_TopLaps,
            'Skidpad_TopLaps'               : Skidpad_TopLaps,
            'Autocross_PointsLeaderboardIC' : Autocross_PointsLeaderboardIC,
            'Autocross_PointsLeaderboardEV' : Autocross_PointsLeaderboardEV,
            'Accel_PointsLeaderboardIC'     : Accel_PointsLeaderboardIC,
            'Accel_PointsLeaderboardEV'     : Accel_PointsLeaderboardEV,
            'Skidpad_PointsLeaderboardIC'   : Skidpad_PointsLeaderboardIC,
            'Skidpad_PointsLeaderboardEV'   : Skidpad_PointsLeaderboardEV,
            'Overall_PointsLeaderboardIC'   : Overall_PointsLeaderboardIC,
            'Overall_PointsLeaderboardEV'   : Overall_PointsLeaderboardEV,
            'ConesLeaderboard'              : ConesLeaderboard
            }