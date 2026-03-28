from app import db
from datetime import datetime, timezone
import json


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    city = db.Column(db.String(100), default="Bratislava")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    holes = db.relationship(
        "Hole", backref="course", lazy=True, cascade="all, delete-orphan",
        order_by="Hole.number"
    )

    @property
    def hole_count(self):
        return len(self.holes)

    @property
    def total_par(self):
        return sum(h.par for h in self.holes)

    def __repr__(self):
        return f"<Course {self.name}>"


class Hole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(200))
    description = db.Column(db.Text)
    par = db.Column(db.Integer, default=3)

    # Start position (where you tee off)
    start_lat = db.Column(db.Float, nullable=False)
    start_lng = db.Column(db.Float, nullable=False)

    # Target position (the "hole" - lamp, sign, etc.)
    target_lat = db.Column(db.Float, nullable=False)
    target_lng = db.Column(db.Float, nullable=False)
    target_description = db.Column(db.String(500))

    bonus_targets = db.relationship(
        "BonusTarget", backref="hole", lazy=True, cascade="all, delete-orphan"
    )

    __table_args__ = (db.UniqueConstraint("course_id", "number"),)

    def __repr__(self):
        return f"<Hole {self.number} on {self.course.name}>"


class BonusTarget(db.Model):
    """Extra targets on a hole that give bonus (negative) or penalty (positive) points."""
    id = db.Column(db.Integer, primary_key=True)
    hole_id = db.Column(db.Integer, db.ForeignKey("hole.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    points = db.Column(db.Integer, nullable=False)  # negative = bonus, positive = penalty
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)

    @property
    def is_bonus(self):
        return self.points < 0

    @property
    def is_penalty(self):
        return self.points > 0

    def __repr__(self):
        kind = "Bonus" if self.is_bonus else "Penalty"
        return f"<{kind}Target {self.name} ({self.points:+d})>"
