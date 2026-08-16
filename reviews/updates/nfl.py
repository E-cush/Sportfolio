import hashlib
import requests
import pandas as pd

from reviews.models import Game


def stable_game_id(source_game_id):
    digest = hashlib.sha256(
        str(source_game_id).encode("utf-8")
    ).digest()

    return int.from_bytes(
        digest[:8],
        byteorder="big",
        signed=False,
    ) & 0x7FFFFFFFFFFFFFFF


def update_nfl(start_date, end_date):
    print(f"Updating NFL ({start_date} → {end_date})...")

    updated = 0
    created = 0

    # ============================================================
    # NFLVERSE — REGULAR SEASON / PLAYOFFS
    # ============================================================

    try:
        df = pd.read_csv(
            "https://github.com/nflverse/nfldata/raw/master/data/games.csv"
        )
    except Exception as e:
        print(f"Failed to retrieve NFL schedule: {e}")
        return

    df = df[
        (df["season"] == 2026) &
        (df["game_type"] != "PRE") &
        (df["gameday"] >= start_date) &
        (df["gameday"] <= end_date)
    ]

    for _, game in df.iterrows():

        game_type = {
            "REG": "Regular Season",
            "WC": "Wild Card",
            "DIV": "Divisional",
            "CON": "Conference Championship",
            "SB": "Super Bowl",
        }.get(
            game["game_type"],
            game["game_type"],
        )

        home_score = (
            0
            if pd.isna(game["home_score"])
            else int(game["home_score"])
        )

        away_score = (
            0
            if pd.isna(game["away_score"])
            else int(game["away_score"])
        )

        status = (
            "Scheduled"
            if pd.isna(game["home_score"])
            else "Final"
        )

        game_id = stable_game_id(game["game_id"])

        rows = Game.objects.filter(
            game_id=game_id,
            league="NFL",
        ).update(
            status=status,
            home_score=home_score,
            away_score=away_score,
            venue=game["stadium"],
            game_type=game_type,
            game_date=game["gameday"],
        )

        updated += rows

    # ============================================================
    # ESPN — PRESEASON
    # ============================================================

    preseason_url = (
        "https://site.api.espn.com/apis/site/v2/sports/"
        "football/nfl/scoreboard"
    )

    preseason_games = []

    try:

        for week in range(1, 5):

            response = requests.get(
                preseason_url,
                params={
                    "dates": "2026",
                    "seasontype": 1,
                    "week": week,
                },
                timeout=30,
            )

            response.raise_for_status()

            week_data = response.json()

            preseason_games.extend(
                week_data.get("events", [])
            )

    except Exception as e:
        print(f"Failed to retrieve NFL preseason: {e}")
        return

    for event in preseason_games:

        season_info = event.get("season", {})

        if isinstance(season_info, dict):

            season_type = season_info.get("type", "")

            if isinstance(season_type, dict):
                event_season_type = str(
                    season_type.get("id", "")
                )
            else:
                event_season_type = str(
                    season_type
                )

        else:
            event_season_type = ""

        if event_season_type != "1":
            continue

        competition = event["competitions"][0]

        home_team = None
        away_team = None

        home_score = 0
        away_score = 0

        for competitor in competition["competitors"]:

            team = competitor["team"]["abbreviation"]

            score = competitor.get("score", 0)

            if competitor["homeAway"] == "home":
                home_team = team

                try:
                    home_score = int(score)
                except (TypeError, ValueError):
                    home_score = 0

            else:
                away_team = team

                try:
                    away_score = int(score)
                except (TypeError, ValueError):
                    away_score = 0

        game_date = (
            pd.to_datetime(event["date"])
            .tz_convert("America/New_York")
            .date()
        )

        venue = (
            competition.get("venue", {})
            .get("fullName", "")
        )

        completed = (
            competition
            .get("status", {})
            .get("type", {})
            .get("completed", False)
        )

        status = (
            "Final"
            if completed
            else "Scheduled"
        )

        game_id = stable_game_id(
            f"ESPN_PRE_{event['id']}"
        )

        rows = Game.objects.filter(
            game_id=game_id,
            league="NFL",
        ).update(
            status=status,
            home_score=home_score,
            away_score=away_score,
            venue=venue,
            game_type="Preseason",
            game_date=game_date,
        )

        updated += rows

    print(f"Updated {updated} NFL games.")