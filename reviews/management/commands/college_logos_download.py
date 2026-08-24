import os
import time

import requests
from django.core.management.base import BaseCommand

from reviews.models import Game


API_BASE = "https://www.thesportsdb.com/api/v1/json/123"

OUTPUT_BASE = os.path.join(
    "static",
    "logos",
    "tsdb",
    "ncaa",
)


class Command(BaseCommand):
    help = "Download college football team logos from TheSportsDB"

    def handle(self, *args, **options):

        games = Game.objects.filter(
            league="NCAA",
            competition="College Football",
        )

        teams = set()

        for game in games:
            if game.home_team:
                teams.add(game.home_team)

            if game.away_team:
                teams.add(game.away_team)

        # Remove obvious non-team placeholders / special event entries.
        ignored = {
            "TBD",
            "EAST All-Stars",
            "East All-Stars",
            "NORTH All-Stars",
            "SOUTH All-Stars",
            "WEST All-Stars",
            "National",
            "Team Gaither",
            "Team Robinson",
        }

        teams -= ignored

        teams = sorted(teams)

        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write("College Football Logo Downloader")
        self.stdout.write("=" * 50)
        self.stdout.write(
            f"Found {len(teams)} college football teams."
        )
        self.stdout.write("")

        successful = 0
        failed = 0

        for index, team_name in enumerate(teams, start=1):

            self.stdout.write(
                f"[{index}/{len(teams)}] {team_name}..."
            )

            try:
                response = requests.get(
                    f"{API_BASE}/searchteams.php",
                    params={"t": team_name},
                    timeout=20,
                )

                response.raise_for_status()

                data = response.json()
                results = data.get("teams") or []

                if not results:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  No TheSportsDB result for {team_name}"
                        )
                    )
                    failed += 1
                    time.sleep(3)
                    continue

                team = results[0]

                badge_url = team.get("strBadge")

                if not badge_url:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  No badge found for {team_name}"
                        )
                    )
                    failed += 1
                    time.sleep(3)
                    continue

                badge_response = requests.get(
                    badge_url,
                    timeout=20,
                )

                badge_response.raise_for_status()

                os.makedirs(
                    OUTPUT_BASE,
                    exist_ok=True,
                )

                filename = (
                    team_name
                    .lower()
                    .replace(" ", "-")
                    .replace("'", "")
                    .replace(".", "")
                    .replace(",", "")
                    .replace("(", "")
                    .replace(")", "")
                    .replace("/", "-")
                    + ".png"
                )

                output_file = os.path.join(
                    OUTPUT_BASE,
                    filename,
                )

                with open(output_file, "wb") as file:
                    file.write(badge_response.content)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Downloaded → {filename}"
                    )
                )

                successful += 1

            except requests.RequestException as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"  Request failed: {e}"
                    )
                )
                failed += 1

            except OSError as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"  File error: {e}"
                    )
                )
                failed += 1

            # Keep comfortably below TheSportsDB rate limits.
            time.sleep(3)

        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write("College football logo download complete.")
        self.stdout.write(f"Successful: {successful}")
        self.stdout.write(f"Failed: {failed}")
        self.stdout.write("=" * 50)