import math

import shapely
from utils import geojson_utils


def postprocess_geojson(json_data, target_area=None, target_centroid=None):
    geometries = [
        shapely.geometry.shape(feature["geometry"]) for feature in json_data["features"]
    ]

    json_data, geometries = normalize_scale(
        json_data, geometries, target_area, target_centroid
    )

    # Get point to place the label
    for index, feature in enumerate(json_data["features"]):
        point = geometries[index].representative_point()
        feature["properties"]["label"] = {"x": point.x, "y": point.y}

    # Fix format of dividers
    if "dividers" in json_data:
        json_data["dividers"] = [json_data["dividers"]]

    return json_data


def normalize_scale(json_data, geometries, target_area=None, target_centroid=None):
    # Scale and translate to match with the target area and centroid
    if not target_area or not target_centroid:
        return json_data, geometries

    geoms_info = geojson_utils.get_geoms_info(geometries)

    scale_factor = math.sqrt(target_area / geoms_info["area"])
    origin_x = geoms_info["centroid"]["x"]
    origin_y = geoms_info["centroid"]["y"]
    diff_x = target_centroid["x"] - origin_x
    diff_y = target_centroid["y"] - origin_y

    for index, feature in enumerate(json_data["features"]):
        geometries[index] = shapely.affinity.scale(
            geometries[index],
            xfact=scale_factor,
            yfact=scale_factor,
            origin=(origin_x, origin_y),
        )
        geometries[index] = shapely.affinity.translate(
            geometries[index],
            xoff=diff_x,
            yoff=diff_y,
        )
        feature["geometry"] = shapely.geometry.mapping(geometries[index])

    if "dividers" in json_data:
        adjusted_dividers = shapely.affinity.scale(
            shapely.geometry.shape(json_data["dividers"]["geometry"]),
            xfact=scale_factor,
            yfact=scale_factor,
            origin=(origin_x, origin_y),
        )
        adjusted_dividers = shapely.affinity.translate(
            adjusted_dividers,
            xoff=diff_x,
            yoff=diff_y,
        )
        json_data["dividers"]["geometry"] = shapely.geometry.mapping(adjusted_dividers)

    # Update bbox
    json_data["bbox"][0] = (
        origin_x + (geoms_info["bbox"][0] - origin_x) * scale_factor
    ) + diff_x
    json_data["bbox"][1] = (
        origin_y + (geoms_info["bbox"][1] - origin_y) * scale_factor
    ) + diff_y
    json_data["bbox"][2] = (
        origin_x + (geoms_info["bbox"][2] - origin_x) * scale_factor
    ) + diff_x
    json_data["bbox"][3] = (
        origin_y + (geoms_info["bbox"][3] - origin_y) * scale_factor
    ) + diff_y

    return json_data, geometries
