#!/usr/bin/env python
import datetime
import json
import logging
import os
import shutil
import traceback
from io import StringIO

import cartogram
import pandas as pd
import settings
import util
from asset import Asset
from database import db
from errors import CartogramError
from flask import Flask, Response, redirect, render_template, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from handler import CartogramHandler
from models import CartogramEntry
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
    app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB
    app.config["MAX_FORM_MEMORY_SIZE"] = 100 * 1024 * 1024

    if settings.USE_DATABASE:
        db.init_app(app)
        Migrate(app, db)

    default_cartogram_handler = "usa"
    cartogram_handler = CartogramHandler()

    try:
        with open(os.path.join(os.path.dirname(__file__), "version.txt")) as f:
            app.config["VERSION"] = " v" + f.read().strip()
    except FileNotFoundError:
        app.config["VERSION"] = ""

    @app.context_processor
    def inject_version():
        return dict(version=app.config["VERSION"])

    @app.route("/", methods=["GET"])
    def index():
        return render_template(
            "welcome.html",
            page_active="home",
            tracking=tracking.determine_tracking_action(request),
        )

    @app.route("/cookies", methods=["GET"])
    def cookies():
        return render_template(
            "cookies.html",
            page_active="",
            tracking=tracking.determine_tracking_action(request),
        )

    app.add_url_rule("/contact", methods=["GET", "POST"], view_func=contact.contact)
    app.add_url_rule("/api/v1/consent", methods=["POST"], view_func=tracking.consent)
    app.add_url_rule(
        "/api/v1/gencaptcha", methods=["GET"], view_func=custom_captcha.gencaptcha
    )

    @app.route("/view", methods=["GET"])
    # Old url
    @app.route("/cartogram", methods=["GET"])
    def get_cartogram():
        return get_cartogram_by_name(default_cartogram_handler, None)

    @app.route("/view/map/<map_name>", methods=["GET"], defaults={"mode": None})
    @app.route("/view/map/<map_name>/<mode>", methods=["GET"])
    # Old urls
    @app.route("/cartogram/map/<map_name>", methods=["GET"], defaults={"mode": None})
    @app.route("/cartogram/map/<map_name>/<mode>", methods=["GET"])
    def get_cartogram_by_name(map_name, mode):
        if mode == "embed":
            template = "embed.html"
        else:
            template = "cartogram.html"

        if not cartogram_handler.has_handler(map_name):
            return Response("Not found", status=404)

        handler_meta = cartogram_handler.get_handler(map_name)
        carto_versions, choro_versions = util.map_types_to_versions(
            handler_meta.get("types", {"cartogram": ["Population (people)"]})
        )

        title = (
            ""
            if not handler_meta.get("hidden", False)
            else handler_meta.get("name", "")
        )

        return render_template(
            template,
            page_active="cartogram",
            maps=cartogram_handler.get_sorted_handler_names(),
            map_name=map_name,
            map_title=title,
            map_color_scheme=handler_meta.get("scheme", "pastel1"),
            carto_versions=carto_versions,
            choro_versions=choro_versions,
            map_spec=handler_meta.get("settings", {}).get("spec", {}),
            mode=mode,
            tracking=tracking.determine_tracking_action(request),
        )

    @app.route("/view/key/<string_key>", methods=["GET"], defaults={"mode": None})
    @app.route("/view/key/<string_key>/<mode>", methods=["GET"])
    # Old urls
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

        map_types = (
            json.loads(cartogram_entry.types)
            if type(cartogram_entry.types) is str
            else {}
        )
        carto_versions, choro_versions = util.map_types_to_versions(map_types)
        map_spec = {}
        if cartogram_entry.settings:
            map_settings = json.loads(cartogram_entry.settings)
            map_spec = map_settings["spec"]

        return render_template(
            template,
            page_active="cartogram",
            maps=cartogram_handler.get_sorted_handler_names(),
            map_name=cartogram_entry.handler,
            map_data_key=string_key,
            map_title=cartogram_entry.title,
            map_color_scheme=cartogram_entry.scheme,
            carto_versions=carto_versions,
            choro_versions=choro_versions,
            map_spec=map_spec,
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

    @app.route("/create", methods=["GET"])
    def create_cartogram():
        return render_template(
            "maker.html",
            page_active="maker",
            maps=cartogram_handler.get_sorted_handler_names(),
            count_limit=settings.CARTOGRAM_COUNT_LIMIT,
            tracking=tracking.determine_tracking_action(request),
        )

    @app.route("/edit/<store_type>/<name_or_key>", methods=["GET"])
    def edit_cartogram(store_type, name_or_key):
        if store_type == "map":
            handler = name_or_key
            handler_meta = cartogram_handler.get_handler(handler)
            csv_url = f"/static/cartdata/{handler}/data.csv"
            title = (
                name_or_key
                if not handler_meta.get("hidden", False)
                else handler_meta.get("name", "")
            )
            scheme = handler_meta.get("scheme", "pastel1")
            map_types = handler_meta.get(
                "types", {"cartogram": ["Population (people)"], "choropleth": []}
            )
            map_settings = handler_meta.get(
                "settings",
                {
                    "isAdvanceMode": False,
                    "scheme": "blues",
                    "type": "quantile",
                    "step": 5,
                    "spec": {},
                },
            )

        elif store_type == "key":
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
            map_types = (
                json.loads(cartogram_entry.types)
                if type(cartogram_entry.types) is str
                else {}
            )
            map_settings = json.loads(cartogram_entry.settings)

        else:
            return Response("Not found", status=404)

        geo_url = cartogram_handler.get_gen_file(handler, name_or_key)[1:]

        return render_template(
            "maker.html",
            page_active="maker",
            maps=cartogram_handler.get_sorted_handler_names(),
            count_limit=settings.CARTOGRAM_COUNT_LIMIT,
            map_name=handler,
            geo_url=geo_url,
            csv_url=csv_url,
            map_title=title,
            map_color_scheme=scheme,
            map_types=map_types,
            map_settings=map_settings,
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

        if "visTypes" not in data:
            return Response(
                '{"error":"Visualization specification not found."}',
                status=400,
                content_type="application/json",
            )

        try:
            vis_types = json.loads(data["visTypes"])
            for key in vis_types:
                for header in vis_types[key]:
                    util.validate_filename(header)

            if (
                "cartogram" in vis_types
                and settings.CARTOGRAM_COUNT_LIMIT
                and len(vis_types["cartogram"]) >= settings.CARTOGRAM_COUNT_LIMIT
            ):
                raise CartogramError(
                    f"Limit of {settings.CARTOGRAM_COUNT_LIMIT} cartograms per data set."
                )
        except CartogramError as e:
            return e.response()
        except Exception:
            return Response(
                '{"error":"Invalid visualization specification."}',
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
            if settings.USE_DATABASE:
                cartogram_entry = CartogramEntry.query.filter_by(
                    string_key=string_key
                ).first()

                if cartogram_entry is not None:
                    raise CartogramError("Duplicated database key.", True)

            if "persist" in data:
                userdata_path = util.get_safepath("static/userdata", string_key)
            else:
                userdata_path = util.get_safepath("tmp", string_key)

            if not os.path.exists(userdata_path):
                os.mkdir(userdata_path)

            with open(util.get_safepath(userdata_path, "data.csv"), "w") as outfile:
                outfile.write(datacsv)

            gen_file = util.get_safepath(
                cartogram_handler.get_gen_file(handler, string_key)
            )

            df = pd.read_csv(StringIO(datacsv))
            cleaned_vis_types = util.clean_map_types(vis_types, df.columns)

            # Manage input file
            if handler == "custom":
                editedFrom = data.get("editedFrom", "")
                if editedFrom and editedFrom != "" and editedFrom != gen_file:
                    edited_path = util.get_safepath(editedFrom.lstrip("/"))
                    shutil.copyfile(edited_path, gen_file)

                else:
                    shutil.copyfile(
                        util.get_safepath("tmp", f"{string_key}.json"), gen_file
                    )
                    clean_by = data.get("geojsonRegionCol", "Region")
            elif "RegionMap" in df.columns and not df["RegionMap"].equals(df["Region"]):
                # If regions are edited, handler should be custom
                handler = "custom"
                new_gen_file = util.get_safepath(
                    cartogram_handler.get_gen_file(handler, string_key)
                )
                shutil.copyfile(gen_file, new_gen_file)
                gen_file = new_gen_file

            cartogram.generate_cartogram(
                datacsv,
                cleaned_vis_types,
                gen_file,
                string_key,
                userdata_path,
                clean_by=clean_by,
            )

            if "persist" in data and settings.USE_DATABASE:
                new_cartogram_entry = CartogramEntry(
                    string_key=string_key,
                    date_created=datetime.datetime.today(),
                    date_accessed=datetime.datetime.now(datetime.UTC)
                    - datetime.timedelta(days=365),
                    handler=handler,
                    title=data.get("title"),
                    scheme=data.get("scheme"),
                    types=json.dumps(cleaned_vis_types),
                    settings=json.dumps(data.get("settings")),
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
                json.dumps(
                    {
                        "error": "Files for cartogram generation not found."
                        + CartogramError.SUGGEST_REFRESH_TXT
                    }
                ),
                status=400,
                content_type="application/json",
            )
        except CartogramError as e:
            db.session.rollback()
            if userdata_path and os.path.exists(userdata_path):
                shutil.rmtree(userdata_path)

            return e.response(app.logger)
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error: {str(e)}\nTraceback:\n{traceback.format_exc()}")
            if userdata_path and os.path.exists(userdata_path):
                shutil.rmtree(userdata_path)

            return Response(
                json.dumps(
                    {"error": "Unknown error." + CartogramError.SUGGEST_REFRESH_TXT}
                ),
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
            file_path = util.get_safepath("tmp", file)
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

    @app.route("/embed/map/<map_name>", methods=["GET"], defaults={"mode": "embed"})
    @app.route("/cartogram/<map_name>", methods=["GET"], defaults={"mode": None})
    def map_old(map_name, mode):
        if not cartogram_handler.has_handler(map_name):
            return Response("Not found", status=404)

        if mode == "embed":
            return redirect(f"/view/map/{map_name}/embed", code=301)
        else:
            return redirect(f"/view/map/{map_name}", code=301)

    @app.route("/cart/<key>", methods=["GET"])
    @app.route("/embed/cart/<key>", methods=["GET"])
    def cartogram_old(key):
        return render_template(
            "404_code_expired.html", title="Outdated share/embed code"
        ), 404

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host=settings.HOST, port=settings.PORT)
