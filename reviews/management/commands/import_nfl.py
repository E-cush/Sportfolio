import hashlib
import requests
import pandas as pd

from django.core.management.base import BaseCommand

from reviews.models import Game


GAME_TYPES = {
    "PRE": "Preseason",
    "REG": "Regular Season",
    "WC": "Wild Card",
    "DIV": "Divisional",
    "CON": "Conference Championship",
    "SB": "Super Bowl",
}


def stable_game_id(source_game_id):
    """
    Create a permanent integer ID from a source game ID.

    Unlike Python's built-in hash(), this produces the same
    value every time the importer runs.
    """
    digest = hashlib.sha256(
        str(source_game_id).encode("utf-8")
    ).digest()

    return int.from_bytes(
        digest[:8],
        byteorder="big",
        signed=False,
    ) & 0x7FFFFFFFFFFFFFFF


class Command(BaseCommand):
    help = "Imports NFL games"

    def handle(self, *args, **kwargs):

        total_games = 0
        updated_games = 0
        created_games = 0

        # ============================================================
        # 1. NFLVERSE — REGULAR SEASON / PLAYOFFS
        # ============================================================

        self.stdout.write("Downloading NFL regular season schedule...")

        df = pd.read_csv(
            "https://github.com/nflverse/nfldata/raw/master/data/games.csv"
        )

        # Current NFL season — regular season/playoffs only
        df = df[
            (df["season"] == 2026) &
            (df["game_type"] != "PRE")
            ]

        for _, game in df.iterrows():

            total_games += 1

            source_game_id = game["game_id"]
            new_game_id = stable_game_id(source_game_id)

            game_type = GAME_TYPES.get(
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

            existing_game = Game.objects.filter(
                league="NFL",
                season=int(game["season"]),
                game_type=game_type,
                home_team=game["home_team"],
                away_team=game["away_team"],
                game_date=game["gameday"],
            ).first()

            defaults = {
                "game_id": new_game_id,
                "league": "NFL",
                "season": int(game["season"]),
                "game_type": game_type,
                "home_team": game["home_team"],
                "away_team": game["away_team"],
                "game_date": game["gameday"],
                "home_score": home_score,
                "away_score": away_score,
                "venue": game["stadium"],
                "status": status,
            }

            if existing_game:

                existing_game.game_id = new_game_id

                for field, value in defaults.items():
                    setattr(existing_game, field, value)

                existing_game.save()

                updated_games += 1

            else:

                Game.objects.create(**defaults)

                created_games += 1

        # ============================================================
        # 2. ESPN — NFL PRESEASON
        # ============================================================

        self.stdout.write("Downloading NFL preseason schedule...")

        preseason_url = (
            "https://site.api.espn.com/apis/site/v2/sports/"
            "football/nfl/scoreboard"
        )

        preseason_games = []

        # ESPN preseason is split into weeks.
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

            week_games = week_data.get("events", [])

            preseason_games.extend(week_games)

            self.stdout.write(
                f"Preseason Week {week}: {len(week_games)} games"
            )

        self.stdout.write(
            f"Found {len(preseason_games)} preseason games."
        )

        valid_preseason_games = 0

        for event in preseason_games:

            # ESPN occasionally returns regular-season games even when
            # seasontype=1 is requested. Only import events that ESPN
            # explicitly identifies as preseason.
            season_info = event.get("season", {})

            if isinstance(season_info, dict):
                season_type = season_info.get("type", "")

                if isinstance(season_type, dict):
                    event_season_type = str(
                        season_type.get("id", "")
                    )
                else:
                    event_season_type = str(season_type)
            else:
                event_season_type = ""

            if event_season_type != "1":
                continue

            valid_preseason_games += 1

            competition = event["competitions"][0]

            competitors = competition["competitors"]

            home_team = None
            away_team = None

            home_score = 0
            away_score = 0

            for competitor in competitors:

                team_abbreviation = competitor["team"]["abbreviation"]

                score = competitor.get("score", 0)

                if competitor["homeAway"] == "home":
                    home_team = team_abbreviation

                    try:
                        home_score = int(score)
                    except (TypeError, ValueError):
                        home_score = 0

                else:
                    away_team = team_abbreviation

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

            source_game_id = f"ESPN_PRE_{event['id']}"

            new_game_id = stable_game_id(source_game_id)

            # Find the existing game by its permanent ESPN-based game ID.
            # This allows us to safely update things like the date.
            existing_game = Game.objects.filter(
                game_id=new_game_id
            ).first()

            defaults = {
                "game_id": new_game_id,
                "league": "NFL",
                "season": 2026,
                "game_type": "Preseason",
                "home_team": home_team,
                "away_team": away_team,
                "game_date": game_date,
                "home_score": home_score,
                "away_score": away_score,
                "venue": venue,
                "status": status,
            }

            if existing_game:

                existing_game.game_id = new_game_id

                for field, value in defaults.items():
                    setattr(existing_game, field, value)

                existing_game.save()

                updated_games += 1

            else:

                Game.objects.create(**defaults)

                created_games += 1

        # ============================================================
        # 3. SUMMARY
        # ============================================================

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {total_games + valid_preseason_games} NFL games!"
            )
        )

        self.stdout.write(
            f"Updated existing games: {updated_games}"
        )

        self.stdout.write(
            f"Created new games: {created_games}"
        )