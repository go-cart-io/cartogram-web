import json
import traceback

from flask import Response


class CartogramError(Exception):
    """Custom exception for user-facing errors with automated logging. DO NOT include sensitive data."""

    def __init__(
        self,
        message: str = "Error occurred",
        logger=None,  # Pass your logger (e.g., Flask's app.logger)
        log_trace: bool = True,  # Enable/disable traceback logging
    ):
        self.message = (
            message
            + " Try refresh this page and re-upload your map and data. If the issue persists, please contact us."
        )
        self.logger = logger
        if logger and log_trace:
            # Log the full traceback if a logger is provided
            self.logger.error(f"Error: {message}\nTraceback:\n{traceback.format_exc()}")
        super().__init__(message)

    def response(self):
        return Response(
            json.dumps({"error": self.message}),
            status=400,
            content_type="application/json",
        )
