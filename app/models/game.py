from app import db
from datetime import datetime, timezone


class Round(db.Model):
    """A player's playthrough of a course."""
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True)
    team_name = db.Column(db.String(100), nullable=True)
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)
    is_complete = db.Column(db.Boolean, default=False)

    course = db.relationship("Course", backref="rounds")
    team = db.relationship("Team", backref="rounds")
    scores = db.relationship("Score", backref="round", lazy=True, cascade="all, delete-orphan")

    @property
    def total_strokes(self):
        return sum(s.strokes for s in self.scores)

    @property
    def total_bonus(self):
        return sum(s.bonus_points for s in self.scores)

    @property
    def total_penalty(self):
        return sum(s.penalty_points for s in self.scores)

    @property
    def total_score(self):
        return sum(s.total for s in self.scores)

    @property
    def vs_par(self):
        if not self.course:
            return 0
        return self.total_score - self.course.total_par

    def __repr__(self):
        return f"<Round {self.player.name} on {self.course.name}>"


class Score(db.Model):
    """Score for a single hole in a round."""
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey("round.id"), nullable=False)
    hole_id = db.Column(db.Integer, db.ForeignKey("hole.id"), nullable=False)
    strokes = db.Column(db.Integer, nullable=False)
    bonus_points = db.Column(db.Integer, default=0)  # negative values (reduce score)
    penalty_points = db.Column(db.Integer, default=0)  # positive values (increase score)
    notes = db.Column(db.Text)

    hole = db.relationship("Hole")

    @property
    def total(self):
        return self.strokes + self.bonus_points + self.penalty_points

    __table_args__ = (db.UniqueConstraint("round_id", "hole_id"),)
