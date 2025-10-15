import datetime
import json
import traceback
import warnings

import settings
from carto import boundary, parser, project
from carto.progress import CartoProgress
from carto.storage import CartoStorage
from errors import CartoError
from flask import Blueprint, Response, current_app, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import CartogramEntry
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


# Handle CustomError specifically
@api_bp.errorhandler(CartoError)
def handle_carto_error(error):
    return error.response(logger=current_app.logger)


# Handle other exceptions
@api_bp.errorhandler(Exception)
def handle_general_error(error):
    current_app.logger.error(
        f"Error: {str(error)}\nTraceback:\n{traceback.format_exc()}"
    )
    return Response(
        json.dumps({"error": "Unknown error."}),
        status=400,
        content_type="application/json",
    )


api_bp.add_url_rule("/api/v1/consent", methods=["POST"], view_func=tracking.consent)
api_bp.add_url_rule(
    "/api/v1/gencaptcha", methods=["GET"], view_func=custom_captcha.gencaptcha
)


@api_bp.route("/api/v1/getprogress", methods=["GET"])
@limiter.exempt
def getprogress():
    progress = CartoProgress(request.args["key"])
    current_progress_output = progress.get()
    return Response(
        json.dumps(current_progress_output),
        status=200,
        content_type="application/json",
    )


@api_bp.route("/api/v1/cartogram/preprocess/<mapDBKey>", methods=["POST"])
def cartogram_preprocess(mapDBKey):
    if "file" not in request.files or request.files["file"].filename == "":
        raise CartoError("No selected file.", log=False)

    mapDBKey = parser.parse_key({"mapDBKey": mapDBKey})
    current_app.logger.info(f"Preprocessing map for {mapDBKey}")

    # Capture warnings during preprocessing to provide user-friendly messages
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        processed_geojson = boundary.preprocess(
            request.files["file"], mapDBKey, request.form.get("maptype", "")
        )

        processed_geojson["warnings"] = []
        for warning_message in w:
            if (
                "Geometry is in a geographic CRS. Results from 'area' are likely incorrect."
                in str(warning_message.message)
            ):
                processed_geojson["warnings"].append(
                    "Geometry is in a geographic CRS. The geographic area calculation (in sq. km) is likely incorrect, but your cartogram will still render accurately."
                )

            elif "More than one layer found" in str(warning_message.message):
                processed_geojson["warnings"].append(
                    "Multiple map layers found. If the preview isn't what you expected, please remove unwanted map layers and re-upload your boundary file."
                )

    current_app.logger.info(f"Finish preprocessing map for {mapDBKey}")
    return Response(
        json.dumps(processed_geojson),
        status=200,
        content_type="application/json",
    )


def cartogram_rate_limit():
    return settings.CARTOGRAM_RATE_LIMIT


@api_bp.route("/api/v1/cartogram", methods=["POST"])
@limiter.limit(cartogram_rate_limit)
def cartogram_gen():
    data = request.get_json()
    handler_name, string_key, vis_types, datacsv, edit_from = parser.parse_project(data)
    clean_by = data.get("geojsonRegionCol", "Region")

    current_app.logger.info(f"Generating cartogram for {string_key}")

    # Prepare data.csv and Input.json in userdata
    storage = CartoStorage(string_key)
    storage.save_tmp("data.csv", datacsv)
    gen_file = storage.standardize_tmp_input(handler_name, edit_from)

    warning_msgs = project.generate(
        datacsv,
        vis_types,
        gen_file,
        string_key,
        storage.tmp_path,
        clean_by=clean_by,
    )

    current_app.logger.info(f"Finish cartogram generation for {string_key}")

    try:
        if "persist" in data:
            storage.persist(handler_name)

            if settings.USE_DATABASE:
                new_cartogram_entry = CartogramEntry(
                    string_key=string_key,
                    date_created=datetime.datetime.today(),
                    date_accessed=datetime.datetime.now(datetime.UTC)
                    - datetime.timedelta(days=365),
                    handler=handler_name,
                    title=data.get("title"),
                    scheme=data.get("scheme"),
                    types=json.dumps(vis_types),
                    settings=json.dumps(data.get("settings")),
                )
                db.session.add(new_cartogram_entry)
                db.session.commit()
        else:
            string_key = None

    except Exception:
        db.session.rollback()
        raise

    return Response(
        json.dumps({"mapDBKey": string_key, "warnings": warning_msgs}),
        status=200,
        content_type="application/json",
    )
