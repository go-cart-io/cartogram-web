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
