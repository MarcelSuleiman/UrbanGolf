from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app import db
from app.models import Player, Team, TeamMember, Course, Hole, Round, Score, BonusTarget
from datetime import datetime, timezone

game_bp = Blueprint("game", __name__)


@game_bp.route("/course/<int:course_id>")
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template("game/course_detail.html", course=course)


@game_bp.route("/start/<int:course_id>", methods=["GET", "POST"])
def start_round(course_id):
    if "player_id" not in session:
        flash("Najprv sa prihlás.", "error")
        return redirect(url_for("player.login"))

    course = Course.query.get_or_404(course_id)
    player = Player.query.get(session["player_id"])

    if request.method == "POST":
        team_id = request.form.get("team_id")
        team_id = int(team_id) if team_id else None

        round_ = Round(
            player_id=player.id,
            course_id=course.id,
            team_id=team_id,
        )
        db.session.add(round_)
        db.session.commit()

        return redirect(url_for("game.play_hole", round_id=round_.id, hole_num=1))

    # Get player's teams
    teams = (
        Team.query.join(Team.members)
        .filter(TeamMember.player_id == player.id)
        .all()
    )
    return render_template("game/start_round.html", course=course, teams=teams)


@game_bp.route("/play/<int:round_id>/hole/<int:hole_num>", methods=["GET", "POST"])
def play_hole(round_id, hole_num):
    if "player_id" not in session:
        flash("Najprv sa prihlás.", "error")
        return redirect(url_for("player.login"))

    round_ = Round.query.get_or_404(round_id)
    if round_.player_id != session["player_id"]:
        flash("Toto nie je tvoje kolo.", "error")
        return redirect(url_for("main.index"))

    hole = Hole.query.filter_by(course_id=round_.course_id, number=hole_num).first_or_404()

    if request.method == "POST":
        strokes = int(request.form.get("strokes", 0))
        bonus_points = int(request.form.get("bonus_points", 0))
        penalty_points = int(request.form.get("penalty_points", 0))
        notes = request.form.get("notes", "").strip()

        existing_score = Score.query.filter_by(round_id=round_.id, hole_id=hole.id).first()
        if existing_score:
            existing_score.strokes = strokes
            existing_score.bonus_points = bonus_points
            existing_score.penalty_points = penalty_points
            existing_score.notes = notes
        else:
            score = Score(
                round_id=round_.id,
                hole_id=hole.id,
                strokes=strokes,
                bonus_points=bonus_points,
                penalty_points=penalty_points,
                notes=notes,
            )
            db.session.add(score)

        db.session.commit()

        # Check if there's a next hole
        next_hole = Hole.query.filter_by(
            course_id=round_.course_id, number=hole_num + 1
        ).first()

        if next_hole:
            return redirect(url_for("game.play_hole", round_id=round_.id, hole_num=hole_num + 1))
        else:
            round_.is_complete = True
            round_.completed_at = datetime.now(timezone.utc)
            db.session.commit()
            return redirect(url_for("game.round_result", round_id=round_.id))

    existing_score = Score.query.filter_by(round_id=round_.id, hole_id=hole.id).first()
    total_holes = len(round_.course.holes)

    return render_template(
        "game/play_hole.html",
        round=round_,
        hole=hole,
        hole_num=hole_num,
        total_holes=total_holes,
        existing_score=existing_score,
    )


@game_bp.route("/result/<int:round_id>")
def round_result(round_id):
    round_ = Round.query.get_or_404(round_id)
    return render_template("game/round_result.html", round=round_)


@game_bp.route("/leaderboard/<int:course_id>")
def leaderboard(course_id):
    course = Course.query.get_or_404(course_id)

    # Individual leaderboard
    completed_rounds = (
        Round.query.filter_by(course_id=course_id, is_complete=True)
        .join(Player)
        .all()
    )
    individual = sorted(completed_rounds, key=lambda r: r.total_score)

    # Team leaderboard
    team_scores = {}
    team_rounds = (
        Round.query.filter_by(course_id=course_id, is_complete=True)
        .filter(Round.team_id.isnot(None))
        .all()
    )
    for r in team_rounds:
        if r.team_id not in team_scores:
            team_scores[r.team_id] = {"team": r.team, "rounds": [], "total": 0}
        team_scores[r.team_id]["rounds"].append(r)
        team_scores[r.team_id]["total"] += r.total_score

    team_leaderboard = sorted(team_scores.values(), key=lambda t: t["total"])

    return render_template(
        "game/leaderboard.html",
        course=course,
        individual=individual,
        team_leaderboard=team_leaderboard,
    )
