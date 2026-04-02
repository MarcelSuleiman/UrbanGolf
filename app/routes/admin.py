from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from app import db
from app.models import Course, Hole, BonusTarget
import json

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
def dashboard():
    courses = Course.query.order_by(Course.created_at.desc()).all()
    return render_template("admin/dashboard.html", courses=courses)


@admin_bp.route("/course/new", methods=["GET", "POST"])
def new_course():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        city = request.form.get("city", "Bratislava").strip()

        if not name:
            flash("Názov trasy je povinný.", "error")
            return redirect(url_for("admin.new_course"))

        course = Course(name=name, description=description, city=city)
        db.session.add(course)
        db.session.commit()

        flash(f'Trasa "{name}" bola vytvorená.', "success")
        return redirect(url_for("admin.edit_course", course_id=course.id))

    return render_template("admin/course_form.html", course=None)


@admin_bp.route("/course/<int:course_id>/edit", methods=["GET", "POST"])
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)

    if request.method == "POST":
        course.name = request.form.get("name", "").strip()
        course.description = request.form.get("description", "").strip()
        course.city = request.form.get("city", "Bratislava").strip()
        course.is_active = "is_active" in request.form
        db.session.commit()

        flash("Trasa bola aktualizovaná.", "success")
        return redirect(url_for("admin.edit_course", course_id=course.id))

    return render_template("admin/course_form.html", course=course)


@admin_bp.route("/course/<int:course_id>/hole/add", methods=["GET", "POST"])
def add_hole(course_id):
    course = Course.query.get_or_404(course_id)

    if request.method == "POST":
        next_number = len(course.holes) + 1

        hole = Hole(
            course_id=course.id,
            number=int(request.form.get("number", next_number)),
            name=request.form.get("name", "").strip(),
            description=request.form.get("description", "").strip(),
            par=int(request.form.get("par", 3)),
            start_lat=float(request.form.get("start_lat", 0)),
            start_lng=float(request.form.get("start_lng", 0)),
            target_lat=float(request.form.get("target_lat", 0)),
            target_lng=float(request.form.get("target_lng", 0)),
            target_description=request.form.get("target_description", "").strip(),
        )
        db.session.add(hole)
        db.session.commit()

        # Add bonus targets
        bonus_names = request.form.getlist("bonus_name[]")
        bonus_points = request.form.getlist("bonus_points[]")
        bonus_descs = request.form.getlist("bonus_desc[]")

        for i, bname in enumerate(bonus_names):
            if bname.strip():
                bt = BonusTarget(
                    hole_id=hole.id,
                    name=bname.strip(),
                    description=bonus_descs[i].strip() if i < len(bonus_descs) else "",
                    points=int(bonus_points[i]) if i < len(bonus_points) else -1,
                )
                db.session.add(bt)

        db.session.commit()
        flash(f"Jamka {hole.number} bola pridaná.", "success")
        return redirect(url_for("admin.edit_course", course_id=course.id))

    next_number = len(course.holes) + 1
    return render_template("admin/hole_form.html", course=course, hole=None, next_number=next_number)


@admin_bp.route("/hole/<int:hole_id>/edit", methods=["GET", "POST"])
def edit_hole(hole_id):
    hole = Hole.query.get_or_404(hole_id)

    if request.method == "POST":
        hole.number = int(request.form.get("number", hole.number))
        hole.name = request.form.get("name", "").strip()
        hole.description = request.form.get("description", "").strip()
        hole.par = int(request.form.get("par", 3))
        hole.start_lat = float(request.form.get("start_lat", 0))
        hole.start_lng = float(request.form.get("start_lng", 0))
        hole.target_lat = float(request.form.get("target_lat", 0))
        hole.target_lng = float(request.form.get("target_lng", 0))
        hole.target_description = request.form.get("target_description", "").strip()

        # Remove old bonus targets and re-add
        BonusTarget.query.filter_by(hole_id=hole.id).delete()

        bonus_names = request.form.getlist("bonus_name[]")
        bonus_points = request.form.getlist("bonus_points[]")
        bonus_descs = request.form.getlist("bonus_desc[]")

        for i, bname in enumerate(bonus_names):
            if bname.strip():
                bt = BonusTarget(
                    hole_id=hole.id,
                    name=bname.strip(),
                    description=bonus_descs[i].strip() if i < len(bonus_descs) else "",
                    points=int(bonus_points[i]) if i < len(bonus_points) else -1,
                )
                db.session.add(bt)

        db.session.commit()
        flash(f"Jamka {hole.number} bola aktualizovaná.", "success")
        return redirect(url_for("admin.edit_course", course_id=hole.course_id))

    return render_template("admin/hole_form.html", course=hole.course, hole=hole, next_number=None)


@admin_bp.route("/hole/<int:hole_id>/delete", methods=["POST"])
def delete_hole(hole_id):
    hole = Hole.query.get_or_404(hole_id)
    course_id = hole.course_id
    db.session.delete(hole)
    db.session.commit()
    flash("Jamka bola odstránená.", "success")
    return redirect(url_for("admin.edit_course", course_id=course_id))


@admin_bp.route("/course/<int:course_id>/export")
def export_course(course_id):
    course = Course.query.get_or_404(course_id)
    data = {
        "name": course.name,
        "description": course.description,
        "city": course.city,
        "holes": [],
    }
    for hole in course.holes:
        hole_data = {
            "number": hole.number,
            "name": hole.name,
            "description": hole.description,
            "par": hole.par,
            "start_lat": hole.start_lat,
            "start_lng": hole.start_lng,
            "target_lat": hole.target_lat,
            "target_lng": hole.target_lng,
            "target_description": hole.target_description,
            "bonuses": [
                {
                    "name": bt.name,
                    "description": bt.description,
                    "points": bt.points,
                }
                for bt in hole.bonus_targets
            ],
        }
        data["holes"].append(hole_data)

    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    import re
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', course.name.lower())
    filename = safe_name + ".json"
    return Response(
        json_str,
        mimetype="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@admin_bp.route("/course/import", methods=["GET", "POST"])
def import_course():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            flash("Vyber JSON súbor.", "error")
            return redirect(url_for("admin.import_course"))

        try:
            data = json.loads(file.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            flash("Neplatný JSON súbor.", "error")
            return redirect(url_for("admin.import_course"))

        course = Course(
            name=data.get("name", "Importovaná trasa"),
            description=data.get("description", ""),
            city=data.get("city", "Bratislava"),
        )
        db.session.add(course)
        db.session.flush()

        for hdata in data.get("holes", []):
            hole = Hole(
                course_id=course.id,
                number=hdata.get("number", 1),
                name=hdata.get("name", ""),
                description=hdata.get("description", ""),
                par=hdata.get("par", 3),
                start_lat=hdata.get("start_lat", 0),
                start_lng=hdata.get("start_lng", 0),
                target_lat=hdata.get("target_lat", 0),
                target_lng=hdata.get("target_lng", 0),
                target_description=hdata.get("target_description", ""),
            )
            db.session.add(hole)
            db.session.flush()

            for bdata in hdata.get("bonuses", []):
                bt = BonusTarget(
                    hole_id=hole.id,
                    name=bdata.get("name", ""),
                    description=bdata.get("description", ""),
                    points=bdata.get("points", 0),
                )
                db.session.add(bt)

        db.session.commit()
        flash(f'Trasa "{course.name}" bola importovaná!', "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/import_course.html")


@admin_bp.route("/course/<int:course_id>/delete", methods=["POST"])
def delete_course(course_id):
    from app.models import Round, Score
    course = Course.query.get_or_404(course_id)
    # Delete all rounds and scores for this course
    rounds = Round.query.filter_by(course_id=course_id).all()
    for r in rounds:
        Score.query.filter_by(round_id=r.id).delete()
    Round.query.filter_by(course_id=course_id).delete()
    db.session.delete(course)
    db.session.commit()
    flash(f'Trasa "{course.name}" bola odstránená.', "success")
    return redirect(url_for("admin.dashboard"))
