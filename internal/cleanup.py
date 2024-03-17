import settings
import datetime
from web import CartogramEntry, db

def cleanup():
    if settings.USE_DATABASE:
        year_ago = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=366)
        CartogramEntry.query.filter(CartogramEntry.date_accessed < year_ago).delete()
        db.session.commit()
        print(year_ago.strftime('%B %d %Y - %H:%M:%S'))
    
cleanup()