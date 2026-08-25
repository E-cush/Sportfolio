import os
import re
import time
import requests

from pathlib import Path
from dotenv import load_dotenv
from django.core.management.base import BaseCommand

from reviews.models import Game


BASE_DIR = Path(__file__).resolve().parents[3]

load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("THESPORTSDB_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "THESPORTSDB_API_KEY was not found in .env"
    )

API_BASE = (
    f"https://www.thesportsdb.com/api/v1/json/{API_KEY}"
)

OUTPUT_BASE = (
    BASE_DIR
    / "static"
    / "logos"
    / "tsdb"
    / "ncaa"
)


IGNORED_TEAMS = {
    "TBD",
    "EAST All-Stars",
    "East All-Stars",
    "NORTH All-Stars",
    "SOUTH All-Stars",
    "WEST All-Stars",
    "West All-Stars",
    "National",
    "Team Gaither",
    "Team Robinson",
}


def clean_filename(team_name):
    """Create a safe filename from the database team name."""

    filename = team_name.lower()

    filename = filename.replace("'", "")
    filename = filename.replace("’", "")

    filename = re.sub(r"[^a-z0-9]+", "-", filename)

    return filename.strip("-") + ".png"


def generate_search_candidates(team_name):
    """
    Generate progressively shorter search names.

    Example:
        American International Yellow Jackets
        -> American International
    """

    candidates = []

    team_name = team_name.strip()

    if not team_name:
        return candidates

    candidates.append(team_name)

    words = team_name.split()

    # Try removing trailing words one at a time.
    # This helps with school + mascot names.
    for i in range(len(words) - 1, 1, -1):

        candidate = " ".join(words[:i])

        if candidate not in candidates:
            candidates.append(candidate)

    # A few common normalization cases.
    aliases = {
        "App State Mountaineers": "Appalachian State",
        "UAlbany Great Danes": "Albany",
        "East Tenn. St. Buccaneers": "East Tennessee State",
        "East Tennessee St. Buccaneers": "East Tennessee State",
        "Florida Intl Golden Panthers": "Florida International",
        "CS-Northridge Matadors": "Cal State Northridge",
        "CSU Northridge Matadors": "Cal State Northridge",
        "UL Monroe Warhawks": "Louisiana-Monroe",
        "Louisiana Monroe Warhawks": "Louisiana-Monroe",
        "Louisiana-Monroe Warhawks": "Louisiana-Monroe",
        "UT Martin Skyhawks": "Tennessee-Martin",
        "Tennessee-Martin Skyhawks": "Tennessee-Martin",
        "San José St Spartans": "San Jose State",
        "San José State Spartans": "San Jose State",
        "St Francis (PA) Red Flash": "Saint Francis",
        "St. Francis (PA) Red Flash": "Saint Francis",
        "Saint Francis Red Flash": "Saint Francis",
        "Stephen F Austin Lumberjacks": "Stephen F. Austin",
        "Stephen F. Austin Lumberjacks": "Stephen F. Austin",
        "Sam Houston Bearkats": "Sam Houston State",
        "Sam Houston State Bearkats": "Sam Houston State",
        "Jacksonville State Gamecocks": "Jacksonville State",
        "Valparaiso Crusaders": "Valparaiso",
    }

    alias = aliases.get(team_name)

    if alias and alias not in candidates:
        candidates.insert(0, alias)

    return candidates


def search_team(team_name):
    """Try multiple names until TheSportsDB finds a team."""

    candidates = generate_search_candidates(team_name)

    for candidate in candidates:

        try:
            response = requests.get(
                f"{API_BASE}/searchteams.php",
                params={"t": candidate},
                timeout=20,
            )

            response.raise_for_status()

            data = response.json()
            teams = data.get("teams") or []

            if teams:
                return teams[0], candidate

        except requests.RequestException:
            continue

    return None, None


class Command(BaseCommand):

    help = "Download NCAA team logos from TheSportsDB"

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

        teams -= IGNORED_TEAMS

        teams = sorted(teams)

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write("NCAA College Football Logo Downloader")
        self.stdout.write("=" * 60)
        self.stdout.write(
            f"Found {len(teams)} unique teams."
        )
        self.stdout.write("")

        OUTPUT_BASE.mkdir(
            parents=True,
            exist_ok=True,
        )

        successful = 0
        skipped = 0
        failed = 0

        for index, team_name in enumerate(
            teams,
            start=1,
        ):

            filename = clean_filename(team_name)

            output_file = OUTPUT_BASE / filename

            self.stdout.write(
                f"[{index}/{len(teams)}] {team_name}..."
            )

            # Don't redownload logos that already exist.
            if output_file.exists():
                self.stdout.write(
                    "  Already downloaded."
                )
                skipped += 1
                continue

            team, matched_name = search_team(team_name)

            if not team:

                self.stdout.write(
                    self.style.WARNING(
                        f"  No TheSportsDB result."
                    )
                )

                failed += 1

                time.sleep(3)

                continue

            badge_url = team.get("strBadge")

            if not badge_url:

                self.stdout.write(
                    self.style.WARNING(
                        "  Team found but no badge."
                    )
                )

                failed += 1

                time.sleep(3)

                continue

            try:

                badge_response = requests.get(
                    badge_url,
                    timeout=20,
                )

                badge_response.raise_for_status()

                with open(
                    output_file,
                    "wb",
                ) as file:

                    file.write(
                        badge_response.content
                    )

                if matched_name != team_name:

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Downloaded using '{matched_name}'"
                            f" → {filename}"
                        )
                    )

                else:

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Downloaded → {filename}"
                        )
                    )

                successful += 1

            except requests.RequestException as e:

                self.stdout.write(
                    self.style.ERROR(
                        f"  Image download failed: {e}"
                    )
                )

                failed += 1

            # Stay safely below the rate limit.
            time.sleep(3)

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write("NCAA logo download complete.")
        self.stdout.write(f"Downloaded:       {successful}")
        self.stdout.write(f"Already existed:  {skipped}")
        self.stdout.write(f"Failed:           {failed}")
        self.stdout.write("=" * 60)