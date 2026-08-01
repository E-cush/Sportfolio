import pandas as pd

from django.core.management.base import BaseCommand

from reviews.models import Game


GAME_TYPES = {
    "REG": "Regular Season",
    "WC": "Wild Card",
    "DIV": "Divisional",
    "CON": "Conference Championship",
    "SB": "Super Bowl",
}


class Command(BaseCommand):
    help = "Imports NFL games"

    def handle(self, *args, **kwargs):

        self.stdout.write("Downloading NFL schedule...")

        df = pd.read_csv(
            "https://github.com/nflverse/nfldata/raw/master/data/games.csv"
        )

        total_games = 0

        for _, game in df.iterrows():

            total_games += 1

            Game.objects.update_or_create(
                game_id=hash(game["game_id"]),
                defaults={
                    "league": "NFL",
                    "season": int(game["season"]),
                    "game_type": GAME_TYPES.get(
                        game["game_type"],
                        game["game_type"],
                    ),
                    "home_team": game["home_team"],
                    "away_team": game["away_team"],
                    "game_date": game["gameday"],
                    "home_score": (
                        0 if pd.isna(game["home_score"])
                        else int(game["home_score"])
                    ),
                    "away_score": (
                        0 if pd.isna(game["away_score"])
                        else int(game["away_score"])
                    ),
                    "venue": game["stadium"],
                    "status": (
                        "Scheduled"
                        if pd.isna(game["home_score"])
                        else "Final"
                    ),
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {total_games} NFL games!"
            )
        )