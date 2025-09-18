import os
from pathlib import Path

import pytest
from errors import CartoError
from utils import file_utils


def test_sanitize_filename():
    filename = 'invalid:/\\*?"<>|name.txt'
    expected = "invalid_________name.txt"
    result = file_utils.sanitize_filename(filename)
    assert result == expected


def test_get_safepath_returns_normalized_path():
    # Test with a path that has 'tmp' prefix and needs normalization
    result = file_utils.get_safepath("tmp", "subdir", "..", "file.txt")

    # Should normalize the path (removing the '..' component)
    expected = os.path.join(Path(__file__).resolve().parent.parent, "tmp/file.txt")
    assert result == expected


def test_get_safepath_raises_error_for_invalid_path_prefix():
    # Test with a path that doesn't start with any allowed prefix
    with pytest.raises(CartoError) as excinfo:
        file_utils.get_safepath("/usr", "local", "bin")

    # Verify the error message
    assert "Invalid file path" in str(excinfo.value)
