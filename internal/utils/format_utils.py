import json
import re


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


# Cleanup so that visTypes only have existing columns, in the same order as csv
def clean_map_types(vis_types, csv_cols):
    based_set = set(csv_cols)
    order_map = {element: i for i, element in enumerate(csv_cols)}

    cleaned_vis_types = {}
    for key in vis_types:
        fields = vis_types[key]

        # Filter the fields to include only elements present in csv
        filtered_fields = [item for item in fields if item in based_set]

        # Sort the fields using a custom key based on the order_map.
        sorted_fields = sorted(filtered_fields, key=lambda x: order_map[x])

        cleaned_vis_types[key] = sorted_fields

    return cleaned_vis_types


def map_types_to_versions(map_types):
    carto_versions = {}
    carto_versions["0"] = {
        "key": "0",
        "header": "Geographic Area (sq. km)",
        "name": "Geographic Area",
        "unit": "sq. km",
    }

    offset = 1
    if "cartogram" in map_types:
        for i, cartogram_label in enumerate(map_types.get("cartogram", [])):
            info = label_to_name_unit(cartogram_label)
            carto_versions[str(i + offset)] = {
                "key": str(i + offset),
                "header": info["header"],
                "name": info["name"],
                "unit": info["unit"],
                "type": "contiguous",
            }

    offset = len(map_types["cartogram"]) + 1
    if "noncontiguous" in map_types:
        for i, cartogram_label in enumerate(map_types.get("noncontiguous", [])):
            info = label_to_name_unit(cartogram_label)
            carto_versions[str(i + offset)] = {
                "key": str(i + offset),
                "header": info["header"],
                "name": info["name"],
                "unit": info["unit"],
                "type": "noncontiguous",
            }

    choro_versions = map_types.get("choropleth", [])

    return carto_versions, choro_versions
