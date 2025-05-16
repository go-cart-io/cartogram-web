import os
from pathlib import Path
import time

import pytest
import util
from errors import CartogramError


def test_sanitize_filename():
    filename = 'invalid:/\\*?"<>|name.txt'
    expected = "invalid_________name.txt"
    result = util.sanitize_filename(filename)
    assert result == expected


def test_get_safepath_returns_normalized_path():
    # Test with a path that has 'tmp' prefix and needs normalization
    result = util.get_safepath("tmp", "subdir", "..", "file.txt")

    # Should normalize the path (removing the '..' component)
    expected = os.path.join(Path(__file__).resolve().parent.parent, "tmp/file.txt")
    assert result == expected


def test_get_safepath_raises_error_for_invalid_path_prefix():
    # Test with a path that doesn't start with any allowed prefix
    with pytest.raises(CartogramError) as excinfo:
        util.get_safepath("/usr", "local", "bin")

    # Verify the error message
    assert "Invalid file path" in str(excinfo.value)


def test_get_csv():
    testdata = {
        "handler": "singaporeRe",
        "values": {
            "fields": [
                {"key": "0", "label": "Region"},
                {"key": "1", "label": "RegionLabel"},
                {"key": "2", "label": "Color"},
                {"key": "3", "label": "Geographic Area (sq. km)"},
                {"key": "4", "label": "Population (people)"},
            ],
            "items": {
                "1": ["CENTRAL REGION", "CR", "#1b9e77", 133.0, 922580.0],
                "2": ["EAST REGION", "ER", "#e7298a", 93.0, 685940.0],
                "3": ["NORTH REGION", "NR", "#d95f02", 135.0, 582330.0],
                "4": ["NORTH-EAST REGION", "NER", "#7570b3", 104.0, 930860.0],
                "5": ["WEST REGION", "WR", "#66a61e", 201.0, 922540.0],
            },
        },
        "mapDBKey": time.time(),
        "persist": "true",
    }
    csvstring = util.get_csv(testdata)
    assert (
        csvstring
        == """Region,RegionLabel,Color,Geographic Area (sq. km),Population (people)
CENTRAL REGION,CR,#1b9e77,133.0,922580.0
EAST REGION,ER,#e7298a,93.0,685940.0
NORTH REGION,NR,#d95f02,135.0,582330.0
NORTH-EAST REGION,NER,#7570b3,104.0,930860.0
WEST REGION,WR,#66a61e,201.0,922540.0"""
    )
