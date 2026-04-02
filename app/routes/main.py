from flask import Blueprint, render_template, session
from app.models import Course, Round

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    courses = Course.query.filter_by(is_active=True).all()
    unfinished_rounds = []
    if "player_id" in session:
        unfinished_rounds = Round.query.filter_by(
            player_id=session["player_id"], is_complete=False
        ).all()
    return render_template("index.html", courses=courses, unfinished_rounds=unfinished_rounds)
