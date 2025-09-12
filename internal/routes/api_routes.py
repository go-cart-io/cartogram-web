import datetime
import json
import os
import shutil
import traceback
from io import StringIO

import pandas as pd
import settings
from carto import boundary, progress, project
from errors import CartoError
from flask import Blueprint, Response, current_app, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from handler import CartogramHandler
from models import CartogramEntry
from utils import file_utils, format_utils
from views import custom_captcha, tracking

api_bp = Blueprint("api", __name__)
db = current_app.extensions["sqlalchemy"]

limiter = Limiter(
    get_remote_address,
    app=current_app,
    default_limits=["100 per hour"],
    storage_uri="redis://{}:{}".format(
        settings.CARTOGRAM_REDIS_HOST, settings.CARTOGRAM_REDIS_PORT
    ),
)

api_bp.add_url_rule("/api/v1/consent", methods=["POST"], view_func=tracking.consent)
api_bp.add_url_rule(
    "/api/v1/gencaptcha", methods=["GET"], view_func=custom_captcha.gencaptcha
)


@api_bp.route("/api/v1/getprogress", methods=["GET"])
@limiter.exempt
def getprogress():
    current_progress_output = progress.getprogress(request.args["key"])
    return Response(
        json.dumps(current_progress_output),
        status=200,
        content_type="application/json",
    )


@api_bp.route("/api/v1/cartogram/preprocess/<mapDBKey>", methods=["POST"])
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
        current_app.logger.info(f"Preprocessing map for {mapDBKey}")
        processed_geojson = boundary.preprocess(request.files["file"], mapDBKey)
        current_app.logger.info(f"Finish preprocessing map for {mapDBKey}")
        return Response(
            json.dumps(processed_geojson),
            status=200,
            content_type="application/json",
        )

    except CartoError as e:
        return e.response(logger=current_app.logger)
    except Exception as e:
        current_app.logger.error(
            f"Error: {str(e)}\nTraceback:\n{traceback.format_exc()}"
        )
        return Response(
            json.dumps({"error": "Unknown error."}),
            status=400,
            content_type="application/json",
        )


def cartogram_rate_limit():
    return settings.CARTOGRAM_RATE_LIMIT


@api_bp.route("/api/v1/cartogram", methods=["POST"])
@limiter.limit(cartogram_rate_limit)
def cartogram_gen():
    cartogram_handler = CartogramHandler()
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
                file_utils.validate_filename(header)

        if (
            "cartogram" in vis_types
            and settings.CARTOGRAM_COUNT_LIMIT
            and len(vis_types["cartogram"]) >= settings.CARTOGRAM_COUNT_LIMIT
        ):
            raise CartoError(
                f"Limit of {settings.CARTOGRAM_COUNT_LIMIT} cartograms per data set."
            )
    except CartoError as e:
        return e.response()
    except Exception:
        return Response(
            '{"error":"Invalid visualization specification."}',
            status=400,
            content_type="application/json",
        )

    datacsv = data["csv"] if "csv" in data else format_utils.get_csv(data)
    string_key = file_utils.sanitize_filename(data["mapDBKey"])
    userdata_path = None
    clean_by = None
    current_app.logger.info(f"Generating cartogram for {string_key}")

    # Prepare data.csv and Input.json in userdata
    # TODO check whether the code works properly if persist is false
    try:
        if settings.USE_DATABASE:
            cartogram_entry = CartogramEntry.query.filter_by(
                string_key=string_key
            ).first()

            if cartogram_entry is not None:
                raise CartoError("Duplicated database key.", True)

        if "persist" in data:
            userdata_path = file_utils.get_safepath("static/userdata", string_key)
        else:
            userdata_path = file_utils.get_safepath("tmp", string_key)

        if not os.path.exists(userdata_path):
            os.mkdir(userdata_path)

        with open(file_utils.get_safepath(userdata_path, "data.csv"), "w") as outfile:
            outfile.write(datacsv)

        gen_file = file_utils.get_safepath(
            cartogram_handler.get_gen_file(handler, string_key)
        )

        df = pd.read_csv(StringIO(datacsv))
        cleaned_vis_types = format_utils.clean_map_types(vis_types, df.columns)

        # Manage input file
        if handler == "custom":
            editedFrom = data.get("editedFrom", "")
            if editedFrom and editedFrom != "" and editedFrom != gen_file:
                edited_path = file_utils.get_safepath(editedFrom.lstrip("/"))
                shutil.copyfile(edited_path, gen_file)

            else:
                shutil.copyfile(
                    file_utils.get_safepath("tmp", f"{string_key}.json"), gen_file
                )
                clean_by = data.get("geojsonRegionCol", "Region")
        elif "RegionMap" in df.columns and not df["RegionMap"].equals(df["Region"]):
            # If regions are edited, handler should be custom
            handler = "custom"
            new_gen_file = file_utils.get_safepath(
                cartogram_handler.get_gen_file(handler, string_key)
            )
            shutil.copyfile(gen_file, new_gen_file)
            gen_file = new_gen_file

        project.generate_cartogram(
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

        current_app.logger.info(f"Finish cartogram generation for {string_key}")
        return Response(
            json.dumps({"mapDBKey": string_key}),
            status=200,
            content_type="application/json",
        )

    except FileNotFoundError as e:
        db.session.rollback()
        current_app.logger.warning(f"Error: {str(e)}")
        return Response(
            json.dumps(
                {
                    "error": "Files for cartogram generation not found."
                    + CartoError.SUGGEST_REFRESH_TXT
                }
            ),
            status=400,
            content_type="application/json",
        )
    except CartoError as e:
        db.session.rollback()
        if userdata_path and os.path.exists(userdata_path):
            shutil.rmtree(userdata_path)

        return e.response(current_app.logger)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error: {str(e)}\nTraceback:\n{traceback.format_exc()}"
        )
        if userdata_path and os.path.exists(userdata_path):
            shutil.rmtree(userdata_path)

        return Response(
            json.dumps({"error": "Unknown error." + CartoError.SUGGEST_REFRESH_TXT}),
            status=400,
            content_type="application/json",
        )
