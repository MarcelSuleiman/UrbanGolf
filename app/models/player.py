from app import db
from datetime import datetime, timezone


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    rounds = db.relationship("Round", backref="player", lazy=True)
    team_memberships = db.relationship("TeamMember", backref="player", lazy=True)

    def __repr__(self):
        return f"<Player {self.name}>"
