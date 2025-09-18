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
