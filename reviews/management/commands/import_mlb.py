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
            "date",
            type=str,
            help="Date to import (YYYY-MM-DD)"
        )

    def handle(self, *args, **kwargs):
        date = kwargs["date"]

        games = statsapi.schedule(
            start_date=date,
            end_date=date
        )

        for game in games:
            Game.objects.update_or_create(
                game_id=game["game_id"],
                defaults={
                    "league": "MLB",
                    "season": int(game["game_date"][:4]),
                    "game_type": GAME_TYPES.get(game["game_type"], "Other"),
                    "home_team": game["home_name"],
                    "away_team": game["away_name"],
                    "game_date": game["game_date"],
                    "home_score": game["home_score"],
                    "away_score": game["away_score"],
                    "venue": game["venue_name"],
                    "status": game["status"],
                }
            )

        self.stdout.write(
            self.style.SUCCESS(f"Imported {len(games)} MLB games!")
        )

