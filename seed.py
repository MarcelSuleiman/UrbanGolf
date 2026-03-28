"""Seed script to create a demo course in Bratislava."""
from app import create_app, db
from app.models import Course, Hole, BonusTarget

app = create_app()

with app.app_context():
    # Check if demo course already exists
    if Course.query.filter_by(name="Staré Mesto Classic").first():
        print("Demo trasa už existuje.")
    else:
        course = Course(
            name="Staré Mesto Classic",
            description="Klasická trasa cez centrum Bratislavy. Od Hlavného námestia cez úzke uličky až po Dunajskú promenádu.",
            city="Bratislava",
        )
        db.session.add(course)
        db.session.flush()

        holes_data = [
            {
                "number": 1,
                "name": "Hlavné námestie",
                "description": "Od fontány Maximiliána k lampe pri Starej radnici.",
                "par": 3,
                "start_lat": 48.14368,
                "start_lng": 17.10886,
                "target_lat": 48.14335,
                "target_lng": 17.10825,
                "target_description": "Zelená lampa pri vchode do Starej radnice",
                "bonuses": [
                    {"name": "Trafíš lampu priamo", "points": -1, "description": "Loptička sa dotkne lampy"},
                    {"name": "Zasiahneš chodca", "points": 2, "description": "Penalizácia za ohrozenie chodca"},
                ],
            },
            {
                "number": 2,
                "name": "Michalská veža",
                "description": "Spod Michalskej brány k stĺpu na konci ulice.",
                "par": 4,
                "start_lat": 48.14475,
                "start_lng": 17.10700,
                "target_lat": 48.14410,
                "target_lng": 17.10755,
                "target_description": "Kovový stĺp pred obchodom",
                "bonuses": [
                    {"name": "Trafíš ceduľu hore", "points": -2, "description": "Bonus za presný zásah značky nad stĺpom"},
                    {"name": "Zasiahneš auto", "points": 3, "description": "Penalizácia za zasiahnutie parkujúceho auta"},
                ],
            },
            {
                "number": 3,
                "name": "Hviezdoslavovo námestie",
                "description": "Od sochy Hviezdoslava ku koši pri lavičke.",
                "par": 3,
                "start_lat": 48.14078,
                "start_lng": 17.10952,
                "target_lat": 48.14022,
                "target_lng": 17.10880,
                "target_description": "Odpadkový kôš pri tretej lavičke",
                "bonuses": [
                    {"name": "Loptička padne do koša", "points": -3, "description": "Jackpot! Priamo do koša."},
                    {"name": "Zasiahneš zviera", "points": 2, "description": "Penalizácia za zasiahnutie holuba alebo psa"},
                ],
            },
            {
                "number": 4,
                "name": "Dunajská promenáda",
                "description": "Od UFO mostu k zábradliu na promenáde.",
                "par": 5,
                "start_lat": 48.13925,
                "start_lng": 17.10475,
                "target_lat": 48.13830,
                "target_lng": 17.10610,
                "target_description": "Červené zábradlie pri schodoch k Dunaju",
                "bonuses": [
                    {"name": "Trafíš zábradlie z diaľky", "points": -1, "description": "Bonus za zásah na prvý pokus"},
                    {"name": "Loptička spadne do Dunaja", "points": 5, "description": "Veľká penalizácia + stratená loptička!"},
                ],
            },
        ]

        for hdata in holes_data:
            bonuses = hdata.pop("bonuses")
            hole = Hole(course_id=course.id, **hdata)
            db.session.add(hole)
            db.session.flush()

            for bdata in bonuses:
                bt = BonusTarget(hole_id=hole.id, **bdata)
                db.session.add(bt)

        db.session.commit()
        print(f"Demo trasa '{course.name}' vytvorená s {len(holes_data)} jamkami!")

    # Draha 2: Petržalka Adventure
    if Course.query.filter_by(name="Petržalka Adventure").first():
        print("Demo trasa 2 už existuje.")
    else:
        course2 = Course(
            name="Petržalka Adventure",
            description="Trasa cez Petržalku – panelákový golf medzi sídliskami, parkami a jazierkami.",
            city="Bratislava",
        )
        db.session.add(course2)
        db.session.flush()

        holes_data2 = [
            {
                "number": 1,
                "name": "Chorvátske rameno",
                "description": "Od lavičky pri Chorvátskom ramene k drevenému stĺpiku na moste.",
                "par": 3,
                "start_lat": 48.12850,
                "start_lng": 17.11200,
                "target_lat": 48.12790,
                "target_lng": 17.11310,
                "target_description": "Drevený stĺpik na pešom moste",
                "bonuses": [
                    {"name": "Trafíš stĺpik na prvý úder", "points": -2, "description": "Presný zásah z diaľky"},
                    {"name": "Loptička padne do ramena", "points": 4, "description": "Stratená loptička vo vode!"},
                ],
            },
            {
                "number": 2,
                "name": "Sad Janka Kráľa",
                "description": "Od fontány pri vstupe k soche v parku.",
                "par": 4,
                "start_lat": 48.13520,
                "start_lng": 17.10450,
                "target_lat": 48.13580,
                "target_lng": 17.10340,
                "target_description": "Kamenná socha v strede parku",
                "bonuses": [
                    {"name": "Trafíš sochu priamo", "points": -1, "description": "Loptička sa dotkne sochy"},
                    {"name": "Trafíš psa venčiaceho sa", "points": 2, "description": "Penalizácia za ohrozenie zvieraťa"},
                    {"name": "Zasiahneš cyklistu", "points": 3, "description": "Penalizácia – cyklotrasa vedie cez park"},
                ],
            },
            {
                "number": 3,
                "name": "Panelákový slalom",
                "description": "Od zastávky Lúky k odpadkovému košu medzi panelákmi.",
                "par": 5,
                "start_lat": 48.12300,
                "start_lng": 17.09800,
                "target_lat": 48.12250,
                "target_lng": 17.09920,
                "target_description": "Žltý odpadkový kôš medzi vchodmi",
                "bonuses": [
                    {"name": "Loptička padne do koša", "points": -3, "description": "Jackpot!"},
                    {"name": "Trafíš okno paneláku", "points": 5, "description": "Veľká penalizácia!"},
                    {"name": "Zasiahneš auto na parkovisku", "points": 3, "description": "Penalizácia za zasiahnutie auta"},
                ],
            },
        ]

        for hdata in holes_data2:
            bonuses = hdata.pop("bonuses")
            hole = Hole(course_id=course2.id, **hdata)
            db.session.add(hole)
            db.session.flush()

            for bdata in bonuses:
                bt = BonusTarget(hole_id=hole.id, **bdata)
                db.session.add(bt)

        db.session.commit()
        print(f"Demo trasa '{course2.name}' vytvorená s {len(holes_data2)} jamkami!")
