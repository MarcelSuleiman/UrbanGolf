from flask import Blueprint, render_template
from app.models import Course

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    courses = Course.query.filter_by(is_active=True).all()
    return render_template("index.html", courses=courses)
