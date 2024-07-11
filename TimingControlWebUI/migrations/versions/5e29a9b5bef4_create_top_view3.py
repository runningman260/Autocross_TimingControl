"""create top view3

Revision ID: 5e29a9b5bef4
Revises: 6467838fa36a
Create Date: 2024-07-11 00:27:17.609311

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5e29a9b5bef4'
down_revision = '6467838fa36a'
branch_labels = None
depends_on = None

def upgrade():
    # SQL statement to create your view
    op.execute("DROP TABLE IF EXISTS top_runs") #remove the "table" from the model to replace it with a view
    op.execute("CREATE VIEW top_runs as SELECT * FROM run_order ORDER BY RAW_TIME LIMIT 10") #obviously needs changed
def downgrade():
    # SQL statement to drop your view
    op.execute("DROP VIEW IF EXISTS top_runs")