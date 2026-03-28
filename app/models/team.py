from app import db
from datetime import datetime, timezone


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    members = db.relationship("TeamMember", backref="team", lazy=True, cascade="all, delete-orphan")

    @property
    def player_names(self):
        return [m.player.name for m in self.members]

    @property
    def member_count(self):
        return len(self.members)

    def __repr__(self):
        return f"<Team {self.name}>"


class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=False)

    __table_args__ = (db.UniqueConstraint("team_id", "player_id"),)
