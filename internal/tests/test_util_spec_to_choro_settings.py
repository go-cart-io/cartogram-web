import json

import pytest
from util import spec_to_choro_settings


def test_spec_to_choro_settings_default():
    # Non-string input should return default settings
    result = spec_to_choro_settings(None)
    assert result == {
        "isAdvanceMode": False,
        "scheme": "blues",
        "type": "quantile",
        "step": 5,
        "spec": "",
    }


def test_spec_to_choro_settings_invalid_json():
    # Invalid JSON string should raise
    with pytest.raises(json.JSONDecodeError):
        spec_to_choro_settings("not a json string")


def test_spec_to_choro_settings_no_scales():
    # JSON with no 'scales' key should return default
    spec = json.dumps({"foo": "bar"})
    result = spec_to_choro_settings(spec)
    assert result == {
        "isAdvanceMode": False,
        "scheme": "blues",
        "type": "quantile",
        "step": 5,
        "spec": "",
    }


def test_spec_to_choro_settings_empty_spec():
    # JSON with 'scales' but empty spec string
    spec = json.dumps({"scales": []})
    result = spec_to_choro_settings(spec)
    assert result == {
        "isAdvanceMode": False,
        "scheme": "blues",
        "type": "quantile",
        "step": 5,
        "spec": "",
    }


def test_spec_to_choro_settings_basic():
    # JSON with one scale, all values the same
    spec = json.dumps(
        {"scales": [{"range": {"scheme": "reds", "count": 7}, "type": "equal"}]}
    )
    result = spec_to_choro_settings(spec)
    assert result["isAdvanceMode"] is False
    assert result["scheme"] == "reds"
    assert result["type"] == "equal"
    assert result["step"] == 7
    # assert result["spec"] == spec


def test_spec_to_choro_settings_advance_mode():
    # JSON with two scales, different values
    spec = json.dumps(
        {
            "scales": [
                {"range": {"scheme": "reds", "count": 7}},
            ]
        }
    )
    result = spec_to_choro_settings(spec)
    assert result["isAdvanceMode"] is True


def test_spec_to_choro_settings_advance_mode_multiple():
    # JSON with two scales, different values
    spec = json.dumps(
        {
            "scales": [
                {"range": {"scheme": "reds", "count": 7}, "type": "equal"},
                {"range": {"scheme": "blues", "count": 5}, "type": "quantile"},
            ]
        }
    )
    result = spec_to_choro_settings(spec)
    assert result["isAdvanceMode"] is True
    assert result["scheme"] == "reds"
    assert result["type"] == "equal"
    assert result["step"] == 7
    # assert result["spec"] == spec
