import time
import requests

from datetime import datetime, timezone as dt_timezone

from django.core.management.base import BaseCommand
from django.utils import timezone

from reviews.models import Game


F1_SCHEDULE_URL = (
    "https://api.jolpi.ca/ergast/f1/{season}.json"
)

F1_WINNERS_URL = (
    "https://api.jolpi.ca/ergast/f1/"
    "{season}/results/1.json"
)


def get_json_with_retry(
    url,
    timeout=30,
    retries=5,
):
    """
    Fetch JSON while handling Jolpica rate limits.
    """

    for attempt in range(retries):

        try:

            response = requests.get(
                url,
                timeout=timeout,
            )

            if response.status_code == 429:

                wait_time = 5 * (
                    attempt + 1
                )

                time.sleep(
                    wait_time
                )

                continue

            response.raise_for_status()

            return response.json()

        except requests.RequestException:

            if attempt == retries - 1:
                raise

            wait_time = 3 * (
                attempt + 1
            )

            time.sleep(
                wait_time
            )

    return None


class Command(BaseCommand):
    help = (
        "Import Formula 1 races "
        "and race winners for a season"
    )

    def add_arguments(
        self,
        parser,
    ):

        parser.add_argument(
            "season",
            type=int,
        )

    def handle(
        self,
        *args,
        **options,
    ):

        season = options[
            "season"
        ]

        self.stdout.write(
            f"Fetching {season} "
            f"Formula 1 schedule..."
        )


        # =====================================================
        # FETCH SCHEDULE
        # =====================================================

        schedule_url = (
            F1_SCHEDULE_URL.format(
                season=season
            )
        )

        try:

            schedule_data = (
                get_json_with_retry(
                    schedule_url
                )
            )

        except requests.RequestException as e:

            self.stdout.write(
                self.style.ERROR(
                    f"F1 schedule request "
                    f"failed: {e}"
                )
            )

            return


        if not schedule_data:

            self.stdout.write(
                self.style.ERROR(
                    "No F1 schedule data "
                    "returned."
                )
            )

            return


        races = (
            schedule_data
            .get("MRData", {})
            .get("RaceTable", {})
            .get("Races", [])
        )


        self.stdout.write(
            f"Found {len(races)} "
            f"F1 races."
        )


        # =====================================================
        # FETCH ALL WINNERS FOR SEASON
        # =====================================================

        winners = {}

        winners_url = (
            F1_WINNERS_URL.format(
                season=season
            )
        )


        # Small pause between schedule and results
        # request to be nice to the API.

        time.sleep(1)


        try:

            winners_data = (
                get_json_with_retry(
                    winners_url
                )
            )


            if winners_data:

                winner_races = (
                    winners_data
                    .get("MRData", {})
                    .get("RaceTable", {})
                    .get("Races", [])
                )


                for winner_race in winner_races:

                    try:

                        round_number = int(
                            winner_race[
                                "round"
                            ]
                        )

                    except (
                        KeyError,
                        ValueError,
                        TypeError,
                    ):

                        continue


                    results = (
                        winner_race.get(
                            "Results",
                            [],
                        )
                    )


                    if not results:
                        continue


                    driver = (
                        results[0]
                        .get(
                            "Driver",
                            {},
                        )
                    )


                    given_name = (
                        driver.get(
                            "givenName",
                            "",
                        )
                    )

                    family_name = (
                        driver.get(
                            "familyName",
                            "",
                        )
                    )


                    winner_name = (
                        f"{given_name} "
                        f"{family_name}"
                    ).strip()


                    if winner_name:

                        winners[
                            round_number
                        ] = winner_name


        except requests.RequestException as e:

            self.stdout.write(
                self.style.WARNING(
                    f"Could not fetch "
                    f"{season} winners: {e}"
                )
            )


        self.stdout.write(
            f"Found winners for "
            f"{len(winners)} races."
        )


        # =====================================================
        # COUNTERS
        # =====================================================

        created = 0
        updated = 0
        skipped = 0


        # =====================================================
        # PROCESS RACES
        # =====================================================

        for race in races:

            try:

                round_number = int(
                    race["round"]
                )

                race_name = (
                    race["raceName"]
                )


                # ---------------------------------------------
                # DATE / START
                # ---------------------------------------------

                race_date = (
                    race["date"]
                )

                race_time = (
                    race.get(
                        "time"
                    )
                )


                if race_time:

                    start_value = (
                        f"{race_date}T"
                        f"{race_time}"
                    )


                    race_start = (
                        datetime.fromisoformat(
                            start_value.replace(
                                "Z",
                                "+00:00",
                            )
                        )
                    )

                else:

                    race_start = (
                        datetime.fromisoformat(
                            race_date
                        )
                    )

                    race_start = (
                        race_start.replace(
                            tzinfo=(
                                dt_timezone.utc
                            )
                        )
                    )


                if race_start.tzinfo is None:

                    race_start = (
                        race_start.replace(
                            tzinfo=(
                                dt_timezone.utc
                            )
                        )
                    )


                # ---------------------------------------------
                # VENUE
                # ---------------------------------------------

                circuit = (
                    race.get(
                        "Circuit",
                        {},
                    )
                )


                circuit_name = (
                    circuit.get(
                        "circuitName",
                        "",
                    )
                )


                location = (
                    circuit.get(
                        "Location",
                        {},
                    )
                )


                locality = (
                    location.get(
                        "locality",
                        "",
                    )
                )


                country = (
                    location.get(
                        "country",
                        "",
                    )
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


                venue = ", ".join(
                    venue_parts
                )


                # ---------------------------------------------
                # WINNER
                # ---------------------------------------------

                race_winner = (
                    winners.get(
                        round_number,
                        "",
                    )
                )


                # ---------------------------------------------
                # STATUS
                # ---------------------------------------------

                now = timezone.now()


                if race_start > now:

                    status = (
                        "Scheduled"
                    )

                else:

                    status = (
                        "Completed"
                    )


                # ---------------------------------------------
                # SPORTFOLIO ID
                # ---------------------------------------------

                game_id = (
                    9_100_000_000_000
                    + (season * 100)
                    + round_number
                )


                # ---------------------------------------------
                # DON'T WIPE AN EXISTING WINNER
                # ---------------------------------------------

                existing_game = (
                    Game.objects.filter(
                        game_id=game_id
                    ).first()
                )


                if (
                    not race_winner
                    and existing_game
                    and existing_game.race_winner
                ):

                    race_winner = (
                        existing_game.race_winner
                    )


                # ---------------------------------------------
                # SAVE
                # ---------------------------------------------

                game, was_created = (
                    Game.objects.update_or_create(
                        game_id=game_id,
                        defaults={
                            "league": (
                                "Racing"
                            ),

                            "competition": (
                                "Formula 1"
                            ),

                            "event_name": (
                                race_name
                            ),

                            "racing_series": (
                                "Formula 1"
                            ),

                            "race_winner": (
                                race_winner
                            ),

                            "season": season,

                            "game_type": (
                                "Grand Prix"
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

                            "venue": venue,

                            "status": status,
                        },
                    )
                )


                if was_created:

                    created += 1

                    action = (
                        "ADDED"
                    )

                else:

                    updated += 1

                    action = (
                        "UPDATED"
                    )


                winner_text = ""


                if race_winner:

                    winner_text = (
                        f" — Winner: "
                        f"{race_winner}"
                    )


                self.stdout.write(
                    f"{action}: "
                    f"{race_name} "
                    f"({race_start.date()})"
                    f"{winner_text}"
                )


            except (
                KeyError,
                ValueError,
                TypeError,
            ) as e:

                skipped += 1


                self.stdout.write(
                    self.style.WARNING(
                        f"Skipped F1 race: "
                        f"{e}"
                    )
                )


        # =====================================================
        # FINISHED
        # =====================================================

        self.stdout.write("")

        self.stdout.write(
            "=" * 40
        )

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

        self.stdout.write(
            "=" * 40
        )


        # Prevent import_racing from hammering
        # Jolpica immediately with the next year.

        time.sleep(2)