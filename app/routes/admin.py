from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Course, Hole, BonusTarget

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


@admin_bp.route("/course/<int:course_id>/delete", methods=["POST"])
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash(f'Trasa "{course.name}" bola odstránená.', "success")
    return redirect(url_for("admin.dashboard"))
