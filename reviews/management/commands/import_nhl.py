import requests

from django.core.management.base import BaseCommand
from reviews.models import Game


class Command(BaseCommand):
    help = "Imports NHL games for a specific date"

    GAME_TYPES = {
        1: "Preseason",
        2: "Regular Season",
        3: "Playoffs",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "date",
            type=str,
            help="Date to import (YYYY-MM-DD)",
        )

    def handle(self, *args, **kwargs):
        date = kwargs["date"]

        try:
            date_compact = date.replace("-", "")

            url = (
                "https://site.api.espn.com/apis/site/v2/"
                f"sports/hockey/nhl/scoreboard?dates={date_compact}"
            )

            response = requests.get(url, timeout=15)
            response.raise_for_status()

            data = response.json()

        except requests.RequestException as exc:
            self.stderr.write(
                self.style.ERROR(
                    f"Failed to fetch NHL schedule: {exc}"
                )
            )
            return

        games = data.get("events", [])

        games = [
            game
            for game in games
            if game.get("status", {})
            .get("type", {})
            .get("description") not in {"OFF", "Canceled"}
        ]

        imported = 0

        for event in games:
            competition = event["competitions"][0]
            competitors = competition["competitors"]

            home = next(
                team
                for team in competitors
                if team["homeAway"] == "home"
            )

            away = next(
                team
                for team in competitors
                if team["homeAway"] == "away"
            )

            home_team = home["team"]["displayName"]
            away_team = away["team"]["displayName"]

            home_score = int(home.get("score", 0))
            away_score = int(away.get("score", 0))

            status = (
                event
                .get("status", {})
                .get("type", {})
                .get("description", "")
            )

            venue = ""

            if competition.get("venue"):
                venue = competition["venue"].get(
                    "fullName",
                    "",
                )

            game_type = self.GAME_TYPES.get(
                event.get("season", {}).get("type"),
                "Regular Season",
            )

            Game.objects.update_or_create(
                game_id=int(event["id"]),
                defaults={
                    "league": "NHL",
                    "season": int(date[:4]),
                    "game_type": game_type,
                    "home_team": home_team,
                    "away_team": away_team,
                    "game_date": date,
                    "home_score": home_score,
                    "away_score": away_score,
                    "venue": venue,
                    "status": status,
                },
            )

            imported += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {imported} NHL games!"
            )
        )