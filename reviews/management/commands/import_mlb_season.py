from datetime import date, timedelta
from django.core.management.base import BaseCommand
import statsapi
from reviews.models import Game

GAME_TYPES = {
    "S": "Preseason",
    "R": "Regular Season",
    "A": "All-Star",
    "F": "Playoffs",
    "D": "Playoffs",
    "L": "Playoffs",
    "W": "Championship",
}


class Command(BaseCommand):
    help = "Imports MLB games"

    def add_arguments(self, parser):
        parser.add_argument(
            "season",
            type=int,
            help="Season to import (e.g. 2026)"
        )

    def handle(self, *args, **kwargs):
        season = kwargs["season"]

        current_day = date(season, 3, 1)
        last_day = date(season, 11, 30)
        total_games = 0

        while current_day <= last_day:
            games = statsapi.schedule(
                start_date=current_day.strftime("%Y-%m-%d"),
                end_date=current_day.strftime("%Y-%m-%d")
            )



            print(f"Importing {current_day} ({len(games)} games)")

            for game in games:
                total_games += 1

                Game.objects.update_or_create(
                    game_id=game["game_id"],
                    defaults={
                        "league": "MLB",
                        "season": season,
                        "game_type": GAME_TYPES.get(game["game_type"], "Other"),
                        "home_team": game["home_name"],
                        "away_team": game["away_name"],
                        "game_date": game["game_date"],
                        "home_score": game["home_score"],
                        "away_score": game["away_score"],
                        "venue": game.get("venue_name") or "Unknown Venue",
                        "status": game["status"],
                    }
                )

            current_day += timedelta(days=1)

        self.stdout.write(
            self.style.SUCCESS(
                f"Season import complete! Imported {total_games} games."
            )
        )