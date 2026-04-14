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
        member_names = [n.strip() for n in request.form.getlist("member") if n.strip()]

        if not team_name:
            flash("Názov tímu je povinný.", "error")
            return redirect(url_for("player.create_team"))

        if len(member_names) < 2:
            flash("Tím musí mať aspoň 2 hráčov.", "error")
            return redirect(url_for("player.create_team"))

        if len(set(member_names)) != len(member_names):
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


@player_bp.route("/teams")
def teams():
    if "player_id" not in session:
        flash("Najprv sa prihlás.", "error")
        return redirect(url_for("player.login"))

    all_teams = Team.query.order_by(Team.name).all()
    current_player_id = session["player_id"]
    return render_template("player/teams.html", teams=all_teams, current_player_id=current_player_id)


@player_bp.route("/team/<int:team_id>/edit", methods=["GET", "POST"])
def edit_team(team_id):
    if "player_id" not in session:
        flash("Najprv sa prihlás.", "error")
        return redirect(url_for("player.login"))

    team = Team.query.get_or_404(team_id)

    if request.method == "POST":
        team_name = request.form.get("team_name", "").strip()
        member_names = [n.strip() for n in request.form.getlist("member") if n.strip()]

        if not team_name:
            flash("Názov tímu je povinný.", "error")
            return redirect(url_for("player.edit_team", team_id=team_id))

        if len(member_names) < 2:
            flash("Tím musí mať aspoň 2 hráčov.", "error")
            return redirect(url_for("player.edit_team", team_id=team_id))

        if len(set(member_names)) != len(member_names):
            flash("Mená hráčov sa nesmú opakovať.", "error")
            return redirect(url_for("player.edit_team", team_id=team_id))

        existing = Team.query.filter(Team.name == team_name, Team.id != team_id).first()
        if existing:
            flash(f'Tím "{team_name}" už existuje.', "error")
            return redirect(url_for("player.edit_team", team_id=team_id))

        players = []
        for name in member_names:
            player = Player.query.filter_by(name=name).first()
            if not player:
                flash(f'Hráč "{name}" neexistuje.', "error")
                return redirect(url_for("player.edit_team", team_id=team_id))
            players.append(player)

        team.name = team_name
        TeamMember.query.filter_by(team_id=team.id).delete()
        for player in players:
            db.session.add(TeamMember(team_id=team.id, player_id=player.id))

        db.session.commit()
        flash(f'Tím "{team_name}" bol aktualizovaný.', "success")
        return redirect(url_for("player.teams"))

    all_players = Player.query.order_by(Player.name).all()
    current_member_ids = {m.player_id for m in team.members}
    return render_template(
        "player/edit_team.html",
        team=team,
        players=all_players,
        current_member_ids=current_member_ids,
    )


@player_bp.route("/team/<int:team_id>/delete", methods=["POST"])
def delete_team(team_id):
    if "player_id" not in session:
        flash("Najprv sa prihlás.", "error")
        return redirect(url_for("player.login"))

    team = Team.query.get_or_404(team_id)
    team_name = team.name

    # TeamMember záznamy sa zmažú automaticky (cascade="all, delete-orphan")
    # Hráči (Player) ostávajú nedotknutí
    db.session.delete(team)
    db.session.commit()

    flash(f'Tím "{team_name}" bol zmazaný.', "success")
    return redirect(url_for("player.teams"))
