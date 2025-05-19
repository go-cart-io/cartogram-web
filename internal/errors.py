import json
import traceback

import settings
from flask import Response


class CartogramError(Exception):
    """Custom exception for user-facing errors with automated logging. DO NOT include sensitive data."""

    def __init__(self, message: str = "Error occurred"):
        self.message = message
        super().__init__(message)

    def response(self, logger=None):
        # Log the full traceback if a logger is provided
        if logger:
            logger.error(self.message)
            if settings.IS_DEBUG:
                logger.error(traceback.format_exc())

        return Response(
            json.dumps({"error": self.message}),
            status=400,
            content_type="application/json",
        )
