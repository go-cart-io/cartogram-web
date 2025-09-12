import os
import re

from errors import CartoError


def sanitize_filename(filename):
    if filename is None:
        return "default_name"

    invalid_chars = r'[\\/:*?\'"<>|]'
    sanitized_filename = re.sub(invalid_chars, "_", str(filename))
    sanitized_filename = sanitized_filename.strip()
    return sanitized_filename


def validate_filename(filename):
    invalid_chars = r'[\\/:*?\'"<>|]'
    if re.search(invalid_chars, filename):
        raise CartoError(
            f"{filename} is invalid. Remove all invalid characters (\\ / : * ? ' \" < > |) to proceed."
        )


def get_safepath(*parts):
    fullpath = os.path.normpath(os.path.join(*parts))
    filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if not os.path.isabs(fullpath):
        fullpath = os.path.join(filepath, fullpath)
    testpath = os.path.abspath(os.path.join(filepath, "..", "test-data"))

    if (
        not fullpath.startswith(filepath + "/tmp")
        and not fullpath.startswith(filepath + "/static")
        and not fullpath.startswith(testpath)
    ):
        raise CartoError(f"Invalid file path: {fullpath}.")

    return fullpath
