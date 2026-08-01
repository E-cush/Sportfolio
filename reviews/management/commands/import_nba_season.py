from datetime import date, timedelta

import requests
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from reviews.models import Game


GAME_TYPES = {
    1: "Preseason",
    2: "Regular Season",
    3: "Playoffs",
}


class Command(BaseCommand):
    help = "Imports NBA games"

    def add_arguments(self, parser):
        parser.add_argument(
            "season",
            type=int,
            help="Season to import (e.g. 2025 for the 2025-26 season)"
        )

    def handle(self, *args, **kwargs):
        season = kwargs["season"]

        current_day = date(season, 10, 1)
        last_day = date(season + 1, 6, 30)

        total_games = 0

        while current_day <= last_day:

            url = (
                "https://site.api.espn.com/apis/site/v2/"
                "sports/basketball/nba/scoreboard"
                f"?dates={current_day.strftime('%Y%m%d')}"
            )

            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()

            except requests.exceptions.RequestException as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"Failed to retrieve {current_day}: {e}"
                    )
                )
                current_day += timedelta(days=1)
                continue

            data = response.json()
            events = data.get("events", [])

            print(f"Importing {current_day} ({len(events)} games)")

            for event in events:

                competitions = event.get("competitions")

                if not competitions:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipping malformed event {event.get('id', 'Unknown ID')}"
                        )
                    )
                    continue

                competition = competitions[0]

                competitors = competition.get("competitors")

                if not competitors:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipping event with no competitors: {event.get('id', 'Unknown ID')}"
                        )
                    )
                    continue

                try:
                    home = next(
                        team for team in competitors
                        if team["homeAway"] == "home"
                    )

                    away = next(
                        team for team in competitors
                        if team["homeAway"] == "away"
                    )
                except StopIteration:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipping event with invalid competitors: {event.get('id', 'Unknown ID')}"
                        )
                    )
                    continue

                season_info = event.get("season", {})

                venue = competition.get(
                    "venue", {}
                ).get(
                    "fullName",
                    "Unknown Venue"
                )

                status = (
                    event.get("status", {})
                    .get("type", {})
                    .get("description", "Unknown")
                )

                game_date = parse_datetime(event.get("date"))

                Game.objects.update_or_create(
                    game_id=event["id"],
                    defaults={
                        "league": "NBA",
                        "season": season,
                        "game_type": GAME_TYPES.get(
                            season_info.get("type"),
                            season_info.get(
                                "slug",
                                "Other"
                            ).replace("-", " ").title()
                        ),
                        "home_team": home["team"]["displayName"],
                        "away_team": away["team"]["displayName"],
                        "game_date": game_date,
                        "home_score": int(home.get("score", 0)),
                        "away_score": int(away.get("score", 0)),
                        "venue": venue,
                        "status": status,
                    },
                )

                total_games += 1

            current_day += timedelta(days=1)

        self.stdout.write(
            self.style.SUCCESS(
                f"Season import complete! Imported {total_games} games."
            )
        )