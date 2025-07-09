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


def get_geoms_info(geometries):
    """
    Get bounding box, centriod, and total area of geojson.
    Alternative to using geopandas. Useful when working with projected map without writing to a file.
    """

    xs = []
    ys = []
    area = 0
    for geom in geometries:
        minx, miny, maxx, maxy = geom.bounds
        xs.extend([minx, maxx])
        ys.extend([miny, maxy])

        area += geom.area

    bbox = [min(xs), min(ys), max(xs), max(ys)]
    centroid = {"x": (bbox[2] + bbox[0]) / 2, "y": (bbox[3] + bbox[1]) / 2}
    return {"bbox": bbox, "centroid": centroid, "area": area}


def union_bounding_boxes(bbox1, bbox2):
    """
    Calculates the union of two bounding boxes.

    Args:
        bbox1 (list): The first bounding box in the format [x_min, y_min, x_max, y_max].
        bbox2 (list): The second bounding box in the format [x_min, y_min, x_max, y_max].

    Returns:
        list: A new bounding box representing the union, in the format [x_min, y_min, x_max, y_max].
    """

    x1_min, y1_min, x1_max, y1_max = bbox1
    x2_min, y2_min, x2_max, y2_max = bbox2
    new_x_min = min(x1_min, x2_min)
    new_y_min = min(y1_min, y2_min)
    new_x_max = max(x1_max, x2_max)
    new_y_max = max(y1_max, y2_max)
    return [new_x_min, new_y_min, new_x_max, new_y_max]


def add_attributes(geojson, is_projected=False, is_world=False):
    if is_projected:
        geojson["crs"] = {"type": "name", "properties": {"name": "EPSG:cartesian"}}
        geojson["properties"] = {
            "note": "Created from go-cart.io with custom projection, not in EPSG:4326."
        }

    if is_world:
        geojson["extent"] = "world"

    return geojson


def label_to_name_unit(label: str):
    """
    Parses a label string to extract the name and unit.

    Args:
        label: The input string, e.g., "Geographic Area (sq. km)".

    Returns:
        A dictionary containing the original header, extracted name, and unit.
    """
    unit_match = re.search(r"\(([^)]+)\)$", label)
    unit = unit_match.group(1).strip() if unit_match else ""
    name = label.replace(f"({unit})", "").strip()
    return {"header": label, "name": name, "unit": unit}


def map_types_to_versions(may_types):
    carto_versions = {}
    carto_versions["0"] = {
        "key": "0",
        "header": "Geographic Area (sq. km)",
        "name": "Geographic Area",
        "unit": "sq. km",
    }
    if "cartogram" in may_types:
        for i, cartogram_label in enumerate(may_types["cartogram"]):
            info = label_to_name_unit(cartogram_label)
            carto_versions[str(i + 1)] = {
                "key": str(i + 1),
                "header": info["header"],
                "name": info["name"],
                "unit": info["unit"],
            }

    choro_versions = {}
    if "choropleth" in may_types:
        for i, cartogram_label in enumerate(may_types["choropleth"]):
            info = label_to_name_unit(cartogram_label)
            choro_versions[str(i)] = {
                "key": str(i),
                "header": info["header"],
                "name": info["name"],
                "unit": info["unit"],
            }

    return carto_versions, choro_versions


def spec_to_choro_settings(spec_str):
    settings = {
        "isAdvanceMode": False,
        "scheme": "blues",
        "type": "quantile",
        "step": 5,
        "spec": "",
    }

    if type(spec_str) is not str:
        return settings

    spec = json.loads(spec_str)
    if (
        "scales" not in spec
        or not isinstance(spec["scales"], list)
        or len(spec["scales"]) == 0
    ):
        return settings

    settings["spec"] = json.dumps(spec_str)[1:-1]
    for index, scale in enumerate(spec["scales"]):
        if index == 0:
            if (
                scale.get("range", {}).get("scheme") is None
                or scale.get("type") is None
                or scale.get("range", {}).get("count") is None
            ):
                settings["isAdvanceMode"] = True
                break

            settings["scheme"] = scale.get("range", {}).get("scheme", "blues")
            settings["type"] = scale.get("type", "quantile")
            settings["step"] = scale.get("range", {}).get("count", 5)
        elif (
            settings["scheme"] != scale.get("range", {}).get("scheme")
            or settings["type"] != scale.get("type")
            or settings["step"] != scale.get("range", {}).get("count")
        ):
            settings["isAdvanceMode"] = True
            break

    return settings
