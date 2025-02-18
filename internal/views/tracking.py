import json

from flask import request, Response

import settings


def consent():
    user_consent = request.form.get("consent", "")

    if user_consent == "yes":
        resp = Response(
            json.dumps(
                {"error": "none", "tracking_id": settings.CARTOGRAM_GA_TRACKING_ID}
            ),
            content_type="application/json",
            status=200,
        )
        resp.set_cookie("tracking", "track", max_age=31556926)  # One year
        return resp
    else:
        resp = Response(
            json.dumps({"error": "none"}), content_type="application/json", status=200
        )
        resp.set_cookie("tracking", "do_not_track", max_age=31556926)
        return resp


def determine_tracking_action(request):
    tracking_setting = request.cookies.get("tracking")

    if tracking_setting is None:
        return {"action": "demand_consent"}

    elif tracking_setting == "track":
        return {"action": "track", "tracking_id": settings.CARTOGRAM_GA_TRACKING_ID}

    else:
        return {"action": "do_not_track"}
