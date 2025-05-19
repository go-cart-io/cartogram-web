import json
import os
import re

from errors import CartogramError


def sanitize_filename(filename):
    if filename is None:
        return "default_name"

    invalid_chars = r'[\\/:*?"<>|]'
    sanitized_filename = re.sub(invalid_chars, "_", str(filename))
    return sanitized_filename


def get_safepath(*parts):
    fullpath = os.path.normpath(os.path.join(*parts))
    filepath = os.path.dirname(__file__)
    if not os.path.isabs(fullpath):
        fullpath = os.path.join(filepath, fullpath)
    
    if (
        not fullpath.startswith(filepath + "/tmp")
        and not fullpath.startswith(filepath + "/static")
        and not fullpath.startswith(filepath + "/tests")
    ):
        raise CartogramError(f"Invalid file path: {fullpath}.")

    return fullpath


def get_csv(data):
    fields = data["values"]["fields"]
    items = data["values"]["items"]

    header = ",".join([field["label"] for field in fields])

    rows = []
    for key, item in items.items():
        row = ",".join(str(value) for value in item)
        rows.append(row)

    return f"{header}\n" + "\n".join(rows)


def convert_col_to_serializable(value):
    try:
        json.dumps(value)
        return value
    except (TypeError, OverflowError):
        return value.astype(str)


def add_attributes(geojson, is_projected=False, is_world=False):
    if is_projected:
        geojson["crs"] = {"type": "name", "properties": {"name": "EPSG:cartesian"}}
        geojson["properties"] = {
            "note": "Created from go-cart.io with custom projection, not in EPSG:4326."
        }

    if is_world:
        geojson["extent"] = "world"

    return geojson
