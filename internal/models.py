from database import db


# Whenever you make changes to the DB models, you must run commands in cartogram-web container as follows:
# export FLASK_APP=web.py
# flask db migrate -m "Migration log"
#    If you get “Target database is not up to date” error, run "flask db stamp head" before migrate
# flask db upgrade
# Remember: you must commit migrations/versions/<your script> to git.
class CartogramEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    string_key = db.Column(db.String(32), unique=True, nullable=False)
    date_created = db.Column(db.DateTime(), nullable=False)
    date_accessed = db.Column(db.DateTime(), server_default="0001-01-01 00:00:00")
    handler = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(120))
    scheme = db.Column(db.String(15))
    types = db.Column(db.Text)
    spec = db.Column(db.Text)

    def __init__(
        self,
        string_key,
        date_created,
        date_accessed,
        handler,
        title,
        scheme,
        types=None,
        spec=None,
    ):
        self.string_key = string_key
        self.date_created = date_created
        self.date_accessed = date_accessed
        self.title = title
        self.scheme = scheme
        self.handler = handler
        self.types = types
        self.spec = spec

    def __repr__(self):
        return "<CartogramEntry {}>".format(self.string_key)
