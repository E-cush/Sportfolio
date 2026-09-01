import csv
import io
import re
import requests

from datetime import datetime, timezone as dt_timezone
from html.parser import HTMLParser

from django.core.management.base import BaseCommand

from reviews.models import Game


NASCAR_CSV_URL = (
    "https://nascar.kylegrealis.com/cup_series.csv"
)

DRIVER_AVERAGES_YEAR_URL = (
    "https://www.driveraverages.com/nascar/"
    "year.php?yr_id={season}"
)


class RaceLinkParser(HTMLParser):
    """
    Collect links to individual NASCAR races from a
    DriverAverages season page.
    """

    def __init__(self):
        super().__init__()
        self.in_race_link = False
        self.current_href = ""
        self.current_text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return

        attrs = dict(attrs)

        href = attrs.get("href", "")

        if "race.php?sked_id=" in href:
            self.in_race_link = True
            self.current_href = href
            self.current_text = []

    def handle_data(self, data):
        if self.in_race_link:
            self.current_text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.in_race_link:

            text = "".join(
                self.current_text
            ).strip()

            self.links.append(
                (
                    self.current_href,
                    text,
                )
            )

            self.in_race_link = False
            self.current_href = ""
            self.current_text = []


def get_season_dates(season):
    """
    Return:

    {
        race_number: datetime,
        ...
    }

    from the DriverAverages season page.
    """

    url = DRIVER_AVERAGES_YEAR_URL.format(
        season=season
    )

    response = requests.get(
        url,
        timeout=20,
        headers={
            "User-Agent": (
                "Mozilla/5.0 Sportfolio/1.0"
            )
        },
    )

    response.raise_for_status()

    parser = RaceLinkParser()
    parser.feed(response.text)

    race_dates = {}

    for href, text in parser.links:

        match = re.search(
            r"sked_id=(\d+)",
            href,
        )

        if not match:
            continue

        sked_id = match.group(1)

        # Normal points races use IDs such as:
        # 1990001
        # 1990010
        #
        # Last three digits are the race number.
        try:
            race_number = int(
                sked_id[-3:]
            )
        except ValueError:
            continue

        # DriverAverages links normally contain text
        # resembling:
        #
        # Feb 18 - Daytona
        #
        date_match = re.search(
            r"([A-Z][a-z]{2})\s+"
            r"(\d{1,2})",
            text,
        )

        if not date_match:
            continue

        month = date_match.group(1)
        day = date_match.group(2)

        try:
            race_date = datetime.strptime(
                f"{month} {day} {season}",
                "%b %d %Y",
            )

        except ValueError:
            continue

        race_date = race_date.replace(
            tzinfo=dt_timezone.utc
        )

        race_dates[race_number] = race_date

    return race_dates


class Command(BaseCommand):
    help = (
        "Import historical NASCAR Cup Series "
        "races from 1949-present"
    )

    def add_arguments(self, parser):

        parser.add_argument(
            "start_year",
            type=int,
        )

        parser.add_argument(
            "end_year",
            type=int,
        )

    def handle(self, *args, **options):

        start_year = options["start_year"]
        end_year = options["end_year"]

        if start_year < 1949:
            start_year = 1949

        if end_year < start_year:
            self.stdout.write(
                self.style.ERROR(
                    "End year must be >= start year."
                )
            )
            return

        self.stdout.write(
            f"Downloading NASCAR Cup history..."
        )

        try:
            response = requests.get(
                NASCAR_CSV_URL,
                timeout=60,
            )

            response.raise_for_status()

        except requests.RequestException as e:

            self.stdout.write(
                self.style.ERROR(
                    f"NASCAR data request failed: {e}"
                )
            )

            return

        reader = csv.DictReader(
            io.StringIO(
                response.text
            )
        )

        # -----------------------------
        # REDUCE DRIVER ROWS TO RACES
        # -----------------------------

        races = {}

        for row in reader:

            try:
                season = int(
                    row["Season"]
                )

                if not (
                    start_year
                    <= season
                    <= end_year
                ):
                    continue

                race_number = int(
                    float(row["Race"])
                )

            except (
                ValueError,
                TypeError,
                KeyError,
            ):
                continue

            key = (
                season,
                race_number,
            )

            # CSV contains one row per driver.
            # We only need one Game per race.
            if key not in races:

                races[key] = {
                    "season": season,
                    "race_number": race_number,
                    "race_name": (
                        row.get("Name")
                        or (
                            f"NASCAR Race "
                            f"{race_number}"
                        )
                    ),
                    "track": (
                        row.get("Track")
                        or "Unknown Track"
                    ),
                }

        self.stdout.write(
            f"Found {len(races)} unique races "
            f"from {start_year}-{end_year}."
        )

        created = 0
        updated = 0
        skipped = 0

        # -----------------------------
        # PROCESS ONE SEASON AT A TIME
        # -----------------------------

        for season in range(
            start_year,
            end_year + 1,
        ):

            season_races = [
                race
                for race in races.values()
                if race["season"] == season
            ]

            if not season_races:
                continue

            self.stdout.write("")
            self.stdout.write(
                f"--- NASCAR {season} ---"
            )

            try:
                race_dates = (
                    get_season_dates(
                        season
                    )
                )

            except requests.RequestException as e:

                self.stdout.write(
                    self.style.WARNING(
                        f"Could not fetch "
                        f"{season} schedule: {e}"
                    )
                )

                continue

            for race in sorted(
                season_races,
                key=lambda x: x[
                    "race_number"
                ],
            ):

                race_number = race[
                    "race_number"
                ]

                race_start = (
                    race_dates.get(
                        race_number
                    )
                )

                if not race_start:

                    skipped += 1

                    self.stdout.write(
                        self.style.WARNING(
                            f"SKIPPED: "
                            f"{race['race_name']} "
                            f"- no date found"
                        )
                    )

                    continue

                race_name = race[
                    "race_name"
                ]

                track_name = race[
                    "track"
                ]

                # Unique NASCAR historical ID.
                #
                # Example:
                # 1990 race 10
                #
                # 920000199010
                game_id = (
                    9_200_000_000_000
                    + (season * 100)
                    + race_number
                )

                game, was_created = (
                    Game.objects.update_or_create(
                        game_id=game_id,
                        defaults={
                            "status": "Completed",

                            "league": "Racing",

                            "competition": (
                                "NASCAR"
                            ),

                            "event_name": (
                                race_name
                            ),

                            "racing_series": (
                                "NASCAR "
                                "Cup Series"
                            ),

                            "season": season,

                            "game_type": (
                                "Race"
                            ),

                            "home_team": "",
                            "away_team": "",

                            "game_date": (
                                race_start.date()
                            ),

                            "game_start": (
                                race_start
                            ),

                            "home_score": 0,
                            "away_score": 0,

                            "venue": (
                                track_name
                            ),
                        },
                    )
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

        self.stdout.write("")
        self.stdout.write(
            "=" * 50
        )

        self.stdout.write(
            "Historical NASCAR "
            "import complete."
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

        self.stdout.write(
            "=" * 50
        )