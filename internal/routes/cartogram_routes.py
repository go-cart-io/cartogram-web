import datetime
import json

import handlers
import settings
from flask import Blueprint, Response, current_app, render_template, request
from models import CartogramEntry
from utils import format_utils
from views import tracking

cartogram_bp = Blueprint("cartogram", __name__)
db = current_app.extensions["sqlalchemy"]
default_cartogram_handler = "usa"


@cartogram_bp.route("/view", methods=["GET"])
# Old url
@cartogram_bp.route("/cartogram", methods=["GET"])
def get_cartogram():
    return get_cartogram_by_name(default_cartogram_handler, None)


@cartogram_bp.route("/view/map/<map_name>", methods=["GET"], defaults={"mode": None})
@cartogram_bp.route("/view/map/<map_name>/<mode>", methods=["GET"])
# Old urls
@cartogram_bp.route(
    "/cartogram/map/<map_name>", methods=["GET"], defaults={"mode": None}
)
@cartogram_bp.route("/cartogram/map/<map_name>/<mode>", methods=["GET"])
def get_cartogram_by_name(map_name, mode):
    if mode == "embed":
        template = "embed.html"
    else:
        template = "viewer.html"

    if not handlers.has_handler(map_name):
        return Response("Not found", status=404)

    handler_meta = handlers.get_handler(map_name)
    carto_versions, choro_versions = format_utils.map_types_to_versions(
        handler_meta.get("types", {"cartogram": ["Population (people)"]})
    )

    title = (
        "" if not handler_meta.get("hidden", False) else handler_meta.get("name", "")
    )

    return render_template(
        template,
        page_active="cartogram",
        page_title=title or "Free Interactive Map Generator",
        maps=handlers.get_sorted_handler_names(),
        map_name=map_name,
        map_title=title,
        map_color_scheme=handler_meta.get("scheme", "pastel1"),
        carto_versions=carto_versions,
        choro_versions=choro_versions,
        map_spec=handler_meta.get("settings", {}).get("spec", {}),
        mode=mode,
        tracking=tracking.determine_tracking_action(request),
    )


@cartogram_bp.route("/view/key/<string_key>", methods=["GET"], defaults={"mode": None})
@cartogram_bp.route("/view/key/<string_key>/<mode>", methods=["GET"])
# Old urls
@cartogram_bp.route(
    "/cartogram/key/<string_key>", methods=["GET"], defaults={"mode": None}
)
@cartogram_bp.route("/cartogram/key/<string_key>/<mode>", methods=["GET"])
def cartogram_by_key(string_key, mode):
    if mode == "embed":
        template = "embed.html"
    else:
        template = "viewer.html"

    if not settings.USE_DATABASE:
        return Response("Not found", status=404)

    cartogram_entry = CartogramEntry.query.filter_by(
        string_key=string_key
    ).first_or_404()

    if cartogram_entry is None or (
        not handlers.has_handler(cartogram_entry.handler)
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
        json.loads(cartogram_entry.types) if type(cartogram_entry.types) is str else {}
    )
    carto_versions, choro_versions = format_utils.map_types_to_versions(map_types)
    map_spec = {}
    if cartogram_entry.settings:
        map_settings = json.loads(cartogram_entry.settings)
        map_spec = map_settings["spec"]

    return render_template(
        template,
        page_active="cartogram",
        page_title=cartogram_entry.title or "Free Interactive Map Generator",
        maps=handlers.get_sorted_handler_names(),
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


@cartogram_bp.route("/create", methods=["GET"])
def create_cartogram():
    return render_template(
        "maker.html",
        page_active="maker",
        maps=handlers.get_sorted_handler_names(),
        count_limit=settings.CARTOGRAM_COUNT_LIMIT,
        tracking=tracking.determine_tracking_action(request),
    )


@cartogram_bp.route("/edit/<store_type>/<name_or_key>", methods=["GET"])
def edit_cartogram(store_type, name_or_key):
    if store_type == "map":
        handler_name = name_or_key
        handler_meta = handlers.get_handler(handler_name)
        csv_url = f"/static/cartdata/{handler_name}/data.csv"
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
            not handlers.has_handler(cartogram_entry.handler)
            and cartogram_entry.handler != "custom"
        ):
            return Response("Invalide map", status=400)

        handler_name = cartogram_entry.handler
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

    geo_url = handlers.get_gen_file(handler_name, name_or_key)[1:]

    return render_template(
        "maker.html",
        page_active="maker",
        maps=handlers.get_sorted_handler_names(),
        count_limit=settings.CARTOGRAM_COUNT_LIMIT,
        map_name=handler_name,
        geo_url=geo_url,
        csv_url=csv_url,
        map_title=title,
        map_color_scheme=scheme,
        map_types=map_types,
        map_settings=map_settings,
        tracking=tracking.determine_tracking_action(request),
    )
