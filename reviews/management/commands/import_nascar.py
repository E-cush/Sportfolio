import requests

from datetime import datetime, timezone as dt_timezone
from django.core.management.base import BaseCommand

from reviews.models import Game


class Command(BaseCommand):
    help = "Import NASCAR Cup Series races"

    def add_arguments(self, parser):
        parser.add_argument(
            "season",
            type=int,
            help="NASCAR season to import, e.g. 2026",
        )

    def handle(self, *args, **options):
        season = options["season"]

        url = (
            f"https://cf.nascar.com/cacher/"
            f"{season}/1/race_list_basic.json"
        )

        self.stdout.write(
            f"Fetching {season} NASCAR Cup Series schedule..."
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
                    f"NASCAR request failed: {e}"
                )
            )
            return

        data = response.json()

        if isinstance(data, list):
            races = data

        elif isinstance(data, dict):
            races = data.get("response", [])

            if isinstance(races, dict):
                races = races.get("races", [])

        else:
            races = []

        self.stdout.write(
            f"Found {len(races)} NASCAR races."
        )

        created = 0
        updated = 0
        skipped = 0

        now = datetime.now(dt_timezone.utc)

        for race in races:
            try:
                race_id = int(race["race_id"])

                race_name = (
                    race.get("race_name")
                    or race.get("race_name_short")
                    or f"NASCAR Race {race_id}"
                )

                track_name = (
                    race.get("track_name")
                    or "Unknown Track"
                )

                start_value = (
                    race.get("race_date")
                    or race.get("date_scheduled")
                )

                if not start_value:
                    raise ValueError(
                        "No race start time found"
                    )

                race_start = datetime.fromisoformat(
                    start_value.replace("Z", "+00:00")
                )

                if race_start.tzinfo is None:
                    race_start = race_start.replace(
                        tzinfo=dt_timezone.utc
                    )

                if now < race_start:
                    status = "Scheduled"
                else:
                    status = "Completed"

                game_id = (
                    9_200_000_000_000
                    + race_id
                )

                game, was_created = Game.objects.update_or_create(
                    game_id=game_id,
                    defaults={
                        "status": status,
                        "league": "Racing",
                        "competition": "NASCAR",
                        "event_name": race_name,
                        "racing_series": "NASCAR Cup Series",
                        "season": season,
                        "game_type": "Race",

                        "home_team": "",
                        "away_team": "",

                        "game_date": race_start.date(),
                        "game_start": race_start,

                        "home_score": 0,
                        "away_score": 0,

                        "venue": track_name,
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
                    f"at {track_name} "
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
                        f"Skipped NASCAR race: {e}"
                    )
                )

        self.stdout.write("")
        self.stdout.write("=" * 40)

        self.stdout.write(
            "NASCAR import complete."
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