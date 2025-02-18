import re
import json
import unicodedata


def sanitize_filename(filename):
    invalid_chars = r'[\\/:*?"<>|]'
    sanitized_filename = re.sub(invalid_chars, "_", filename)
    return sanitized_filename


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


def remove_accents(text):
    # example usage
    # data_df = data_df.sort_values(by=‘Region’, key=lambda col: col.apply(remove_accents))
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
