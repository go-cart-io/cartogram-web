import datetime
import os
import shutil

import settings
from database import db
from flask import Blueprint, Response, redirect, render_template
from handler import CartogramHandler
from utils import file_utils

maintenance_bp = Blueprint("maintenance", __name__)


@maintenance_bp.route("/cleanup", methods=["GET"])
def cleanup():
    # Delete records in the database and files that the accessed date is older than 1 year
    num_records = 0
    year_ago = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=366)
    if settings.USE_DATABASE:
        try:
            from models import CartogramEntry

            records = CartogramEntry.query.filter(
                getattr(CartogramEntry, "date_accessed") < year_ago
            ).all()
            num_records = len(records)
            for record in records:
                folder_path = f"static/userdata/{record.string_key}"
                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)
                db.session.delete(record)

            db.session.commit()

        except Exception:
            db.session.rollback()

    # Delete files in folder tmp that the created date is older than 1 days
    for file in os.listdir("tmp"):
        file_path = file_utils.get_safepath("tmp", file)
        days_ago = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1)
        try:
            mod_time = os.stat(file_path).st_mtime
            if mod_time < days_ago.timestamp():
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                else:
                    shutil.rmtree(file_path)

        except Exception as e:
            print(e)

    return "{} ({} records)".format(
        year_ago.strftime("%d %B %Y - %H:%M:%S"), num_records
    )


@maintenance_bp.route(
    "/embed/map/<map_name>", methods=["GET"], defaults={"mode": "embed"}
)
@maintenance_bp.route("/cartogram/<map_name>", methods=["GET"], defaults={"mode": None})
def map_old(map_name, mode):
    cartogram_handler = CartogramHandler()
    if not cartogram_handler.has_handler(map_name):
        return Response("Not found", status=404)

    if mode == "embed":
        return redirect(f"/view/map/{map_name}/embed", code=301)
    else:
        return redirect(f"/view/map/{map_name}", code=301)


@maintenance_bp.route("/cart/<key>", methods=["GET"])
@maintenance_bp.route("/embed/cart/<key>", methods=["GET"])
def cartogram_old(key):
    return render_template(
        "404_code_expired.html", title="Outdated share/embed code"
    ), 404
