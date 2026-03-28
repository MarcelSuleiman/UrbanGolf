from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models import Player, Team, TeamMember

player_bp = Blueprint("player", __name__)


@player_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Meno je povinné.", "error")
            return redirect(url_for("player.register"))

        if len(name) > 50:
            flash("Meno môže mať maximálne 50 znakov.", "error")
            return redirect(url_for("player.register"))

        existing = Player.query.filter_by(name=name).first()
        if existing:
            flash(f'Hráč s menom "{name}" už existuje. Zvol si iné meno.', "error")
            return redirect(url_for("player.register"))

        player = Player(name=name)
        db.session.add(player)
        db.session.commit()

        session["player_id"] = player.id
        session["player_name"] = player.name
        flash(f"Vitaj, {name}!", "success")
        return redirect(url_for("main.index"))

    return render_template("player/register.html")


@player_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        player = Player.query.filter_by(name=name).first()
        if not player:
            flash(f'Hráč "{name}" neexistuje. Zaregistruj sa najprv.', "error")
            return redirect(url_for("player.login"))

        session["player_id"] = player.id
        session["player_name"] = player.name
        flash(f"Vitaj späť, {name}!", "success")
        return redirect(url_for("main.index"))

    return render_template("player/login.html")


@player_bp.route("/logout")
def logout():
    session.clear()
    flash("Bol si odhlásený.", "info")
    return redirect(url_for("main.index"))


@player_bp.route("/team/create", methods=["GET", "POST"])
def create_team():
    if "player_id" not in session:
        flash("Najprv sa prihlás.", "error")
        return redirect(url_for("player.login"))

    if request.method == "POST":
        team_name = request.form.get("team_name", "").strip()
        member_names = [
            request.form.get(f"member_{i}", "").strip() for i in range(1, 5)
        ]
        member_names = [n for n in member_names if n]

        if not team_name:
            flash("Názov tímu je povinný.", "error")
            return redirect(url_for("player.create_team"))

        if len(member_names) != 4:
            flash("Tím musí mať presne 4 hráčov.", "error")
            return redirect(url_for("player.create_team"))

        if len(set(member_names)) != 4:
            flash("Mená hráčov sa nesmú opakovať.", "error")
            return redirect(url_for("player.create_team"))

        existing_team = Team.query.filter_by(name=team_name).first()
        if existing_team:
            flash(f'Tím "{team_name}" už existuje.', "error")
            return redirect(url_for("player.create_team"))

        players = []
        for name in member_names:
            player = Player.query.filter_by(name=name).first()
            if not player:
                flash(f'Hráč "{name}" neexistuje. Všetci členovia sa musia najprv zaregistrovať.', "error")
                return redirect(url_for("player.create_team"))
            players.append(player)

        team = Team(name=team_name)
        db.session.add(team)
        db.session.flush()

        for player in players:
            member = TeamMember(team_id=team.id, player_id=player.id)
            db.session.add(member)

        db.session.commit()
        flash(f'Tím "{team_name}" bol vytvorený!', "success")
        return redirect(url_for("main.index"))

    players = Player.query.order_by(Player.name).all()
    return render_template("player/create_team.html", players=players)
