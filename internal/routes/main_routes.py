from flask import Blueprint, render_template, request
from views import contact, tracking

main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET"])
def index():
    return render_template(
        "welcome.html",
        page_active="home",
        tracking=tracking.determine_tracking_action(request),
    )


@main_bp.route("/cookies", methods=["GET"])
def cookies():
    return render_template(
        "cookies.html",
        page_active="",
        tracking=tracking.determine_tracking_action(request),
    )


main_bp.add_url_rule("/contact", methods=["GET", "POST"], view_func=contact.contact)
