from database import db

# Whenever you make changes to the DB models, you must run commands in cartogram-web container as follows:
# export FLASK_APP=web.py
# flask db migrate -m "Migration log"
# flask db upgrade
class CartogramEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    string_key = db.Column(db.String(32), unique=True, nullable=False)
    date_created = db.Column(db.DateTime(), nullable=False)
    date_accessed = db.Column(db.DateTime(), server_default='0001-01-01 00:00:00')        
    handler = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(120))
    scheme = db.Column(db.String(15))

    def __repr__(self):
        return '<CartogramEntry {}>'.format(self.string_key)