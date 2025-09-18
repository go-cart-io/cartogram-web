import os
import shutil

import handlers
from errors import CartoError
from utils import file_utils


class CartoStorage:
    """
    A storage management class for handling temporary and persistent file operations.
    Manages file paths, temporary directories, and data persistence for cartographic projects.

    Attributes:
        string_key (str): Unique identifier used for creating safe file paths
        tmp_path (str): Path to the temporary directory for this storage instance
    """

    def __init__(self, string_key: str):
        """
        Initialize CartoStorage with a unique string key.

        Args:
            string_key (str): Unique identifier for this storage instance,
                            used to create isolated temporary directories
        """
        self.string_key = string_key
        self.tmp_path = file_utils.get_safepath("tmp", self.string_key)

    def create_tmp(self) -> None:
        """
        Create the temporary directory if it doesn't already exist.
        Uses the tmp_path attribute to determine the directory location.
        """
        if not os.path.exists(self.tmp_path):
            os.mkdir(self.tmp_path)

    def get_safe_tmp_file_path(self, filename: str) -> str:
        """
        Generate a safe file path within the temporary directory.

        Args:
            filename (str): Name of the file to create a path for

        Returns:
            str: Safe file path combining tmp_path and filename
        """
        return file_utils.get_safepath(self.tmp_path, filename)

    def save_tmp(self, filename: str, data: str) -> None:
        """
        Save data to a file in the temporary directory.
        Creates the temporary directory if it doesn't exist.

        Args:
            filename (str): Name of the file to save
            data (str): String data to write to the file
        """
        self.create_tmp()
        with open(self.get_safe_tmp_file_path(filename), "w") as outfile:
            outfile.write(data)

    def standardize_tmp_input(
        self, handler_name: str, edit_from: str | None = None
    ) -> str:
        """
        Standardize input by copying appropriate source files to temporary Input.json.
        Handles different scenarios: predefined handlers, custom handlers, and editing
        from existing projects.

        Args:
            handler_name (str): Name of the handler to use ('custom' for custom handlers)
            edit_from (str, optional): Path to existing file to edit from

        Returns:
            str: Path to the standardized Input.json file

        Raises:
            CartoError: If source files are not found or operations fail
        """
        gen_file = self.get_safe_tmp_file_path("Input.json")

        try:
            if handlers.has_handler(handler_name):
                # Copy input file if editing from existing cartdata handler
                original_file = file_utils.get_safepath(
                    handlers.get_gen_file(handler_name)
                )

                self.create_tmp()
                shutil.copyfile(original_file, gen_file)
            elif (
                handler_name == "custom"
                and edit_from
                and edit_from != ""
                and edit_from != gen_file
            ):
                # Copy input file if editing from an existing project
                edited_path = file_utils.get_safepath(edit_from.lstrip("/"))
                shutil.copyfile(edited_path, gen_file)
        except FileNotFoundError:
            raise CartoError("File not found. Please re-upload the boundary.")

        if not os.path.exists(gen_file):
            raise CartoError("File not found.", suggest_refresh=True)

        return gen_file

    def persist(self, handler: str) -> None:
        """
        Move temporary files to permanent storage location.
        Cleans up temporary Input.json for non-custom handlers and moves
        the entire temporary directory to user data storage.

        Args:
            handler (str): Handler type ('custom' or predefined handler name)

        Raises:
            CartoError: If temporary files don't exist
        """
        if not os.path.exists(self.tmp_path):
            raise CartoError("Files not found.", suggest_refresh=True)

        # Remove Input.json for non-custom handlers since they use cartdata
        if handler != "custom":
            os.remove(self.get_safe_tmp_file_path("Input.json"))

        # Move temporary directory to permanent user data location
        user_path = file_utils.get_safepath("static/userdata", self.string_key)
        shutil.move(self.tmp_path, user_path)

        return
