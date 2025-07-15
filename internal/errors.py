import json
import traceback

import settings
from flask import Response


class CartogramError(Exception):
    """Custom exception for user-facing errors with automated logging. DO NOT include sensitive data."""

    SUGGEST_REFRESH_TXT = " Try refresh this page, then re-upload your map and data. If the issue persists, please contact us."

    def __init__(self, message: str = "Error occurred", suggest_refresh=False):
        if not message.endswith("."):
            message = message + "."

        if suggest_refresh:
            message = message + self.SUGGEST_REFRESH_TXT

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
