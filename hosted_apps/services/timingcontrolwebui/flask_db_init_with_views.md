flask db init
flask db migrate
flask db revision -m "give it a name"

open the revision file made, alter with below (or similar)

def upgrade():
    # SQL statement to create your view
    op.execute("DROP TABLE IF EXISTS top_runs") #remove the "table" from the model to replace it with a view
    op.execute("CREATE VIEW top_runs as SELECT * FROM run_order ORDER BY RAW_TIME LIMIT 10") #obviously needs changed
def downgrade():
    # SQL statement to drop your view
    op.execute("DROP VIEW IF EXISTS top_runs")

flask db migrate
flask db upgrade