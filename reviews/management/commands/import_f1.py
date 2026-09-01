import requests

from datetime import datetime, timezone as dt_timezone
from django.core.management.base import BaseCommand

from reviews.models import Game


JOLPICA_URL = "https://api.jolpi.ca/ergast/f1/{season}.json"


class Command(BaseCommand):
    help = "Import Formula 1 races from Jolpica"

    def add_arguments(self, parser):
        parser.add_argument(
            "season",
            type=int,
            help="F1 season to import, e.g. 2026",
        )

    def handle(self, *args, **options):
        season = options["season"]

        url = JOLPICA_URL.format(season=season)

        self.stdout.write(
            f"Fetching {season} Formula 1 schedule..."
        )

        try:
            response = requests.get(
                url,
                timeout=20,
            )
            response.raise_for_status()

        except requests.RequestException as e:
            self.stdout.write(
                self.style.ERROR(
                    f"F1 request failed: {e}"
                )
            )
            return

        data = response.json()

        races = (
            data
            .get("MRData", {})
            .get("RaceTable", {})
            .get("Races", [])
        )

        self.stdout.write(
            f"Found {len(races)} F1 races."
        )

        created = 0
        updated = 0
        skipped = 0

        now = datetime.now(dt_timezone.utc)

        for race in races:
            try:
                round_number = int(race["round"])

                race_name = race["raceName"]

                race_date = race["date"]
                race_time = race.get("time", "00:00:00Z")

                race_start = datetime.fromisoformat(
                    f"{race_date}T"
                    f"{race_time.replace('Z', '+00:00')}"
                )

                circuit = race.get(
                    "Circuit",
                    {}
                )

                circuit_name = circuit.get(
                    "circuitName",
                    ""
                )

                location = circuit.get(
                    "Location",
                    {}
                )

                locality = location.get(
                    "locality",
                    ""
                )

                country = location.get(
                    "country",
                    ""
                )

                venue_parts = [
                    part
                    for part in [
                        circuit_name,
                        locality,
                        country,
                    ]
                    if part
                ]

                venue = ", ".join(venue_parts)

                # Give racing events their own ID namespace so they
                # cannot collide with MLB/NBA/etc API IDs.
                game_id = (
                    9_100_000_000_000
                    + (season * 100)
                    + round_number
                )

                if now < race_start:
                    status = "Scheduled"
                else:
                    status = "Completed"

                game, was_created = Game.objects.update_or_create(
                    game_id=game_id,
                    defaults={
                        "status": status,
                        "league": "Racing",
                        "competition": "Formula 1",
                        "event_name": race_name,
                        "racing_series": "Formula 1",
                        "season": season,
                        "game_type": "Grand Prix",

                        # Racing does not use home/away teams,
                        # but these fields are required by the
                        # current Game model.
                        "home_team": "",
                        "away_team": "",

                        "game_date": race_start.date(),
                        "game_start": race_start,

                        # Racing does not use team scores.
                        "home_score": 0,
                        "away_score": 0,

                        "venue": venue,
                    },
                )

                if was_created:
                    created += 1
                    action = "ADDED"
                else:
                    updated += 1
                    action = "UPDATED"

                self.stdout.write(
                    f"{action}: "
                    f"{race_name} "
                    f"({race_start.date()})"
                )

            except (
                KeyError,
                ValueError,
                TypeError,
            ) as e:
                skipped += 1

                self.stdout.write(
                    self.style.WARNING(
                        f"Skipped F1 race: {e}"
                    )
                )

        self.stdout.write("")
        self.stdout.write("=" * 40)

        self.stdout.write(
            "Formula 1 import complete."
        )

        self.stdout.write(
            f"Created: {created}"
        )

        self.stdout.write(
            f"Updated: {updated}"
        )

        self.stdout.write(
            f"Skipped: {skipped}"
        )

        self.stdout.write("=" * 40)