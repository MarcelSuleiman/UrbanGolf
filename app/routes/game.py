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

    # Check for unfinished round on this course
    unfinished = Round.query.filter_by(
        player_id=player.id, course_id=course.id, is_complete=False
    ).first()

    if request.method == "POST":
        action = request.form.get("action", "new")

        if action == "continue" and unfinished:
            # Find next unplayed hole
            played_holes = {s.hole.number for s in unfinished.scores}
            next_hole = 1
            for h in course.holes:
                if h.number not in played_holes:
                    next_hole = h.number
                    break
            else:
                # All holes played, go to last one to review/finish
                next_hole = course.holes[-1].number
            return redirect(url_for("game.play_hole", round_id=unfinished.id, hole_num=next_hole))

        # Start new round (abandon old one if exists)
        if unfinished:
            Score.query.filter_by(round_id=unfinished.id).delete()
            db.session.delete(unfinished)
            db.session.commit()

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
    return render_template("game/start_round.html", course=course, teams=teams, unfinished=unfinished)


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
        bonus_points = -abs(int(request.form.get("bonus_points", 0)))
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

        # If editing a previous hole, return to the hole the player came from
        return_hole = request.form.get("return_hole", type=int)
        if return_hole:
            return redirect(url_for("game.play_hole", round_id=round_.id, hole_num=return_hole))

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
    played_scores = sorted(
        [s for s in round_.scores if s.hole.number != hole_num],
        key=lambda s: s.hole.number,
    )

    return render_template(
        "game/play_hole.html",
        round=round_,
        hole=hole,
        hole_num=hole_num,
        total_holes=total_holes,
        existing_score=existing_score,
        played_scores=played_scores,
    )


@game_bp.route("/result/<int:round_id>")
def round_result(round_id):
    round_ = Round.query.get_or_404(round_id)
    return render_template("game/round_result.html", round=round_)


@game_bp.route("/leaderboard/<int:course_id>")
def leaderboard(course_id):
    course = Course.query.get_or_404(course_id)

    # Individual leaderboard - completed
    completed_rounds = (
        Round.query.filter_by(course_id=course_id, is_complete=True)
        .join(Player)
        .all()
    )
    individual = sorted(completed_rounds, key=lambda r: r.total_score)

    # In-progress rounds
    in_progress = (
        Round.query.filter_by(course_id=course_id, is_complete=False)
        .join(Player)
        .all()
    )
    in_progress = [r for r in in_progress if r.scores]
    in_progress = sorted(in_progress, key=lambda r: r.total_score)

    # Team leaderboard — group all rounds (any state, with at least 1 score) by team
    all_team_rounds_grouped = {}
    all_team_rounds = (
        Round.query.filter(
            Round.course_id == course_id,
            Round.team_id.isnot(None),
        ).all()
    )
    for r in all_team_rounds:
        if not r.scores:
            continue
        tid = r.team_id
        if tid not in all_team_rounds_grouped:
            all_team_rounds_grouped[tid] = {
                "team": r.team,
                "rounds": [],
                "total": 0,
                "has_incomplete": False,
            }
        all_team_rounds_grouped[tid]["rounds"].append(r)
        all_team_rounds_grouped[tid]["total"] += r.total_score
        if not r.is_complete:
            all_team_rounds_grouped[tid]["has_incomplete"] = True

    # Compute average score per player for each team entry
    for v in all_team_rounds_grouped.values():
        count = len(v["rounds"])
        v["player_count"] = count
        v["average"] = round(v["total"] / count, 2) if count else 0

    # Completed teams: all members with rounds have finished
    team_leaderboard = sorted(
        [v for v in all_team_rounds_grouped.values() if not v["has_incomplete"]],
        key=lambda t: t["average"],
    )
    # In-progress teams: at least one member still playing
    team_inprogress = sorted(
        [v for v in all_team_rounds_grouped.values() if v["has_incomplete"]],
        key=lambda t: t["average"],
    )

    return render_template(
        "game/leaderboard.html",
        course=course,
        individual=individual,
        in_progress=in_progress,
        team_leaderboard=team_leaderboard,
        team_inprogress=team_inprogress,
    )


@game_bp.route("/abandon/<int:round_id>", methods=["POST"])
def abandon_round(round_id):
    if "player_id" not in session:
        flash("Najprv sa prihlás.", "error")
        return redirect(url_for("player.login"))

    round_ = Round.query.get_or_404(round_id)
    if round_.player_id != session["player_id"]:
        flash("Toto nie je tvoje kolo.", "error")
        return redirect(url_for("main.index"))

    Score.query.filter_by(round_id=round_.id).delete()
    db.session.delete(round_)
    db.session.commit()
    flash("Hra bola ukončená.", "info")
    return redirect(url_for("main.index"))
