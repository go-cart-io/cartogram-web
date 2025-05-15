#!/usr/bin/env python
import datetime
import json
import logging
import os
import shutil
import traceback

import cartogram
import settings
import util
from asset import Asset
from errors import CartogramError
from flask import Flask, Response, render_template, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from handler import CartogramHandler
from views import contact, custom_captcha, tracking
from werkzeug.middleware.proxy_fix import ProxyFix


def create_app():
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    Asset(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["100 per hour"],
        storage_uri="redis://{}:{}".format(
            settings.CARTOGRAM_REDIS_HOST, settings.CARTOGRAM_REDIS_PORT
        ),
    )

    app.app_context().push()
    app.logger.setLevel(logging.INFO)
    app.secret_key = settings.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URI
    # This gets rid of an annoying Flask error message. We don't need this feature anyway.
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["ENV"] = "development" if settings.IS_DEBUG else "production"
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB
    app.config["MAX_FORM_MEMORY_SIZE"] = 10 * 1024 * 1024

    if settings.USE_DATABASE:
        from database import db
        from models import CartogramEntry

        db.init_app(app)
        Migrate(app, db)

        try:
            db.create_all()
        except Exception as err:
            app.logger.error(err)

    default_cartogram_handler = "usa"
    cartogram_handler = CartogramHandler()

    @app.route("/", methods=["GET"])
    def index():
        return render_template(
            "welcome.html",
            page_active="home",
            tracking=tracking.determine_tracking_action(request),
        )

    @app.route("/about", methods=["GET"])
    def about():
        return render_template(
            "about.html",
            page_active="about",
            tracking=tracking.determine_tracking_action(request),
        )

    @app.route("/cookies", methods=["GET"])
    def cookies():
        return render_template(
            "cookies.html",
            page_active="",
            tracking=tracking.determine_tracking_action(request),
        )

    @app.route("/faq", methods=["GET"])
    def faq():
        return render_template(
            "faq.html",
            page_active="faq",
            tracking=tracking.determine_tracking_action(request),
        )

    app.add_url_rule("/contact", methods=["GET", "POST"], view_func=contact.contact)
    app.add_url_rule("/api/v1/consent", methods=["POST"], view_func=tracking.consent)
    app.add_url_rule(
        "/api/v1/gencaptcha", methods=["GET"], view_func=custom_captcha.gencaptcha
    )

    @app.route("/cartogram", methods=["GET"])
    def get_cartogram():
        return get_cartogram_by_name(default_cartogram_handler, None)

    @app.route("/cartogram/map/<map_name>", methods=["GET"], defaults={"mode": None})
    @app.route("/cartogram/map/<map_name>/<mode>", methods=["GET"])
    def get_cartogram_by_name(map_name, mode):
        if mode == "embed":
            template = "embed.html"
        else:
            template = "cartogram.html"

        if not cartogram_handler.has_handler(map_name):
            return Response("Not found", status=404)

        return render_template(
            template,
            page_active="cartogram",
            maps=cartogram_handler.get_sorted_handler_names(),
            map_name=map_name,
            mode=mode,
            tracking=tracking.determine_tracking_action(request),
        )

    @app.route("/cartogram/key/<string_key>", methods=["GET"], defaults={"mode": None})
    @app.route("/cartogram/key/<string_key>/<mode>", methods=["GET"])
    def cartogram_by_key(string_key, mode):
        if mode == "embed":
            template = "embed.html"
        else:
            template = "cartogram.html"

        if not settings.USE_DATABASE:
            return Response("Not found", status=404)

        cartogram_entry = CartogramEntry.query.filter_by(
            string_key=string_key
        ).first_or_404()

        if cartogram_entry is None or (
            not cartogram_handler.has_handler(cartogram_entry.handler)
            and cartogram_entry.handler != "custom"
        ):
            return Response("Invalide map", status=400)

        if mode != "preview":
            try:
                cartogram_entry.date_accessed = datetime.datetime.now(datetime.UTC)
                db.session.commit()
            except Exception:
                db.session.rollback()

        return render_template(
            template,
            page_active="cartogram",
            maps=cartogram_handler.get_sorted_handler_names(),
            map_name=cartogram_entry.handler,
            map_data_key=string_key,
            map_title=cartogram_entry.title,
            map_color_scheme=cartogram_entry.scheme,
            mode=mode,
            tracking=tracking.determine_tracking_action(request),
        )

    @app.route("/api/v1/getprogress", methods=["GET"])
    @limiter.exempt
    def getprogress():
        current_progress_output = cartogram.getprogress(request.args["key"])
        return Response(
            json.dumps(current_progress_output),
            status=200,
            content_type="application/json",
        )

    def cartogram_rate_limit():
        return settings.CARTOGRAM_RATE_LIMIT

    @app.route("/cartogram/create", methods=["GET"])
    def create_cartogram():
        return render_template(
            "maker.html",
            page_active="maker",
            maps=cartogram_handler.get_sorted_handler_names(),
            tracking=tracking.determine_tracking_action(request),
        )

    @app.route("/cartogram/edit/<type>/<name_or_key>", methods=["GET"])
    def edit_cartogram(type, name_or_key):
        if type == "map":
            handler = name_or_key
            csv_url = f"/static/cartdata/{handler}/data.csv"
            title = name_or_key
            scheme = "pastel1"

        elif type == "key":
            if not settings.USE_DATABASE:
                return Response("Not found", status=404)

            cartogram_entry = CartogramEntry.query.filter_by(
                string_key=name_or_key
            ).first_or_404()

            if cartogram_entry is None or (
                not cartogram_handler.has_handler(cartogram_entry.handler)
                and cartogram_entry.handler != "custom"
            ):
                return Response("Invalide map", status=400)

            handler = cartogram_entry.handler
            csv_url = f"/static/userdata/{name_or_key}/data.csv"
            title = cartogram_entry.title
            scheme = cartogram_entry.scheme if cartogram_entry.scheme else "pastel1"

        else:
            return Response("Not found", status=404)

        geo_url = cartogram_handler.get_gen_file(handler, name_or_key)[1:]

        return render_template(
            "maker.html",
            page_active="maker",
            maps=cartogram_handler.get_sorted_handler_names(),
            map_name=handler,
            geo_url=geo_url,
            csv_url=csv_url,
            map_title=title,
            map_color_scheme=scheme,
            tracking=tracking.determine_tracking_action(request),
        )

    @app.route("/api/v1/cartogram/preprocess/<mapDBKey>", methods=["POST"])
    def cartogram_preprocess(mapDBKey):
        if mapDBKey is None or mapDBKey == "":
            return Response(
                '{"error":"Missing sharing key."}',
                status=400,
                content_type="application/json",
            )

        if "file" not in request.files or request.files["file"].filename == "":
            return Response(
                '{"error": "No selected file."}',
                status=400,
                content_type="application/json",
            )

        try:
            app.logger.info(f"Preprocessing map for {mapDBKey}")
            processed_geojson = cartogram.preprocess(request.files["file"], mapDBKey)
            app.logger.info(f"Finish preprocessing map for {mapDBKey}")
            return Response(
                json.dumps(processed_geojson),
                status=200,
                content_type="application/json",
            )

        except CartogramError as e:
            return e.response(logger=app.logger)
        except Exception as e:
            app.logger.error(f"Error: {str(e)}\nTraceback:\n{traceback.format_exc()}")
            return Response(
                json.dumps({"error": "Unknown error."}),
                status=400,
                content_type="application/json",
            )

    @app.route("/api/v1/cartogram", methods=["POST"])
    @limiter.limit(cartogram_rate_limit)
    def cartogram_gen():
        data = request.get_json()
        handler = data["handler"]

        if "handler" not in data or (
            not cartogram_handler.has_handler(handler) and handler != "custom"
        ):
            return Response(
                '{"error":"Invalid map."}', status=400, content_type="application/json"
            )

        if "mapDBKey" not in data:
            return Response(
                '{"error":"Missing sharing key."}',
                status=400,
                content_type="application/json",
            )

        datacsv = data["csv"] if "csv" in data else util.get_csv(data)
        string_key = util.sanitize_filename(data["mapDBKey"])
        userdata_path = None
        clean_by = None
        app.logger.info(f"Generating cartogram for {string_key}")

        # Prepare data.csv and Input.json in userdata
        # TODO check whether the code works properly if persist is false
        try:
            if "persist" in data:
                userdata_path = util.get_safepath("static/userdata", string_key)
            else:
                userdata_path = util.get_safepath("/tmp", string_key)

            if not os.path.exists(userdata_path):
                os.mkdir(userdata_path)

            with open(util.get_safepath(userdata_path, "data.csv"), "w") as outfile:
                outfile.write(datacsv)

            gen_file = util.get_safepath(
                cartogram_handler.get_gen_file(handler, string_key)
            )

            if handler == "custom":
                editedFrom = data.get("editedFrom", "")
                if editedFrom and editedFrom != "" and editedFrom != gen_file:
                    edited_path = util.get_safepath("./", editedFrom)
                    shutil.copyfile(edited_path, gen_file)

                else:
                    shutil.copyfile(
                        util.get_safepath("/tmp", f"{string_key}.json"), gen_file
                    )
                    clean_by = data.get("geojsonRegionCol", "Region")

            cartogram.generate_cartogram(
                datacsv, gen_file, string_key, userdata_path, clean_by=clean_by
            )

            if "persist" in data and settings.USE_DATABASE:
                new_cartogram_entry = CartogramEntry(
                    string_key=string_key,
                    date_created=datetime.datetime.today(),
                    date_accessed=datetime.datetime.now(datetime.UTC)
                    - datetime.timedelta(days=365),
                    title=data["title"],
                    scheme=data["scheme"],
                    handler=handler,
                )
                db.session.add(new_cartogram_entry)
                db.session.commit()
            else:
                string_key = None

            app.logger.info(f"Finish cartogram generation for {string_key}")
            return Response(
                json.dumps({"mapDBKey": string_key}),
                status=200,
                content_type="application/json",
            )

        except FileNotFoundError as e:
            db.session.rollback()
            app.logger.warning(f"Error: {str(e)}")
            return Response(
                '{"error":"Files for cartogram generation not found."}',
                status=400,
                content_type="application/json",
            )
        except CartogramError as e:
            db.session.rollback()
            return e.response(app.logger)
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error: {str(e)}\nTraceback:\n{traceback.format_exc()}")
            if os.path.exists(userdata_path):
                shutil.rmtree(userdata_path)

            return Response(
                json.dumps({"error": "Unknown error."}),
                status=400,
                content_type="application/json",
            )

    @app.route("/cleanup", methods=["GET"])
    def cleanup():
        # Delete records in the database and files that the accessed date is older than 1 year
        num_records = 0
        year_ago = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=366)
        if settings.USE_DATABASE:
            try:
                records = CartogramEntry.query.filter(
                    CartogramEntry.date_accessed < year_ago
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

        # Delete files in folder /tmp that the created date is older than 1 days
        for file in os.listdir("/tmp"):
            file_path = util.get_safepath("/tmp", file)
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

    @app.route("/cart/<key>", methods=["GET"])
    @app.route("/embed/map/<key>", methods=["GET"])
    @app.route("/embed/cart/<key>", methods=["GET"])
    def cartogram_old(key):
        return render_template(
            "404_code_expired.html", title="Outdated share/embed code"
        ), 404

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=settings.IS_DEBUG, host=settings.HOST, port=settings.PORT)
