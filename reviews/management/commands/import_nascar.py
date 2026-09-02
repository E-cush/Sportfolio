import time
import requests

from datetime import datetime, timezone as dt_timezone
from django.core.management.base import BaseCommand

from reviews.models import Game


def get_json_with_retry(
    url,
    timeout=20,
    retries=4,
):
    for attempt in range(retries):

        try:
            response = requests.get(
                url,
                timeout=timeout,
            )

            if response.status_code == 429:
                wait_time = 5 * (attempt + 1)

                time.sleep(wait_time)

                continue

            response.raise_for_status()

            return response.json()

        except requests.RequestException:

            if attempt == retries - 1:
                raise

            time.sleep(
                2 * (attempt + 1)
            )

    return None


def extract_race_winner(data):
    """
    Extract the finishing-position-1 driver
    from a NASCAR weekend feed.
    """

    if not isinstance(data, dict):
        return ""


    # -----------------------------------------
    # MOST COMMON WEEKEND FEED STRUCTURE
    # -----------------------------------------

    weekend_race = data.get(
        "weekend_race"
    )

    if weekend_race:

        if isinstance(
            weekend_race,
            dict,
        ):
            race_objects = [
                weekend_race
            ]

        elif isinstance(
            weekend_race,
            list,
        ):
            race_objects = (
                weekend_race
            )

        else:
            race_objects = []


        for race_object in race_objects:

            if not isinstance(
                race_object,
                dict,
            ):
                continue

            results = (
                race_object.get(
                    "results",
                    [],
                )
            )

            winner = (
                find_winner_in_results(
                    results
                )
            )

            if winner:
                return winner


    # -----------------------------------------
    # POSSIBLE TOP-LEVEL RACE OBJECT
    # -----------------------------------------

    race_object = data.get(
        "race"
    )

    if isinstance(
        race_object,
        dict,
    ):

        winner = (
            find_winner_in_results(
                race_object.get(
                    "results",
                    [],
                )
            )
        )

        if winner:
            return winner


    # -----------------------------------------
    # POSSIBLE TOP-LEVEL RESULTS
    # -----------------------------------------

    winner = (
        find_winner_in_results(
            data.get(
                "results",
                [],
            )
        )
    )

    if winner:
        return winner


    return ""


def find_winner_in_results(results):

    if not isinstance(
        results,
        list,
    ):
        return ""


    for result in results:

        if not isinstance(
            result,
            dict,
        ):
            continue


        position = (
            result.get(
                "finishing_position"
            )
        )


        try:
            position = int(
                position
            )

        except (
            TypeError,
            ValueError,
        ):
            continue


        if position != 1:
            continue


        winner = (
            result.get(
                "driver_fullname"
            )
            or result.get(
                "driver_name"
            )
            or result.get(
                "full_name"
            )
            or ""
        )


        return winner.strip()


    return ""


class Command(BaseCommand):

    help = (
        "Import NASCAR Cup Series races "
        "and race winners"
    )


    def add_arguments(
        self,
        parser,
    ):

        parser.add_argument(
            "season",
            type=int,
            help=(
                "NASCAR season to import, "
                "e.g. 2026"
            ),
        )


    def handle(
        self,
        *args,
        **options,
    ):

        season = options[
            "season"
        ]


        schedule_url = (
            f"https://cf.nascar.com/cacher/"
            f"{season}/1/"
            f"race_list_basic.json"
        )


        self.stdout.write(
            f"Fetching {season} "
            f"NASCAR Cup Series schedule..."
        )


        # =========================================
        # SCHEDULE
        # =========================================

        try:

            data = get_json_with_retry(
                schedule_url
            )

        except requests.RequestException as e:

            self.stdout.write(
                self.style.ERROR(
                    f"NASCAR request failed: "
                    f"{e}"
                )
            )

            return


        if isinstance(
            data,
            list,
        ):

            races = data


        elif isinstance(
            data,
            dict,
        ):

            races = data.get(
                "response",
                [],
            )

            if isinstance(
                races,
                dict,
            ):

                races = races.get(
                    "races",
                    [],
                )


        else:

            races = []


        self.stdout.write(
            f"Found {len(races)} "
            f"NASCAR races."
        )


        created = 0
        updated = 0
        skipped = 0
        winner_count = 0


        now = datetime.now(
            dt_timezone.utc
        )


        # =========================================
        # RACES
        # =========================================

        for race in races:

            try:

                race_id = int(
                    race[
                        "race_id"
                    ]
                )


                race_name = (
                    race.get(
                        "race_name"
                    )
                    or race.get(
                        "race_name_short"
                    )
                    or (
                        f"NASCAR Race "
                        f"{race_id}"
                    )
                )


                track_name = (
                    race.get(
                        "track_name"
                    )
                    or "Unknown Track"
                )


                start_value = (
                    race.get(
                        "race_date"
                    )
                    or race.get(
                        "date_scheduled"
                    )
                )


                if not start_value:

                    raise ValueError(
                        "No race start time found"
                    )


                race_start = (
                    datetime.fromisoformat(
                        start_value.replace(
                            "Z",
                            "+00:00",
                        )
                    )
                )


                if (
                    race_start.tzinfo
                    is None
                ):

                    race_start = (
                        race_start.replace(
                            tzinfo=(
                                dt_timezone.utc
                            )
                        )
                    )


                # =================================
                # STATUS
                # =================================

                if now < race_start:

                    status = (
                        "Scheduled"
                    )

                else:

                    status = (
                        "Completed"
                    )


                # =================================
                # SPORTFOLIO GAME ID
                # =================================

                game_id = (
                    9_200_000_000_000
                    + race_id
                )


                # =================================
                # WINNER
                # =================================

                race_winner = ""


                if status == "Completed":

                    winner_url = (
                        f"https://cf.nascar.com/"
                        f"cacher/{season}/1/"
                        f"{race_id}/"
                        f"weekend-feed.json"
                    )


                    try:

                        winner_data = (
                            get_json_with_retry(
                                winner_url
                            )
                        )


                        if winner_data:

                            race_winner = (
                                extract_race_winner(
                                    winner_data
                                )
                            )


                    except (
                        requests.RequestException
                    ):

                        race_winner = ""


                    # Be gentle with NASCAR's
                    # public cacher.

                    time.sleep(0.35)


                # =================================
                # PRESERVE EXISTING WINNER
                # =================================

                existing_game = (
                    Game.objects.filter(
                        game_id=game_id
                    ).first()
                )


                if (
                    not race_winner
                    and existing_game
                    and (
                        existing_game
                        .race_winner
                    )
                ):

                    race_winner = (
                        existing_game
                        .race_winner
                    )


                # =================================
                # SAVE
                # =================================

                game, was_created = (
                    Game.objects
                    .update_or_create(
                        game_id=game_id,

                        defaults={
                            "status": (
                                status
                            ),

                            "league": (
                                "Racing"
                            ),

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

                            "race_winner": (
                                race_winner
                            ),

                            "season": (
                                season
                            ),

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

                    winner_count += 1

                    winner_text = (
                        f" — Winner: "
                        f"{race_winner}"
                    )


                self.stdout.write(
                    f"{action}: "
                    f"{race_name} "
                    f"at {track_name} "
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
                        f"Skipped NASCAR "
                        f"race: {e}"
                    )
                )


        # =========================================
        # FINISHED
        # =========================================

        self.stdout.write("")

        self.stdout.write(
            "=" * 40
        )


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
            f"Winners found: "
            f"{winner_count}"
        )


        self.stdout.write(
            f"Skipped: {skipped}"
        )


        self.stdout.write(
            "=" * 40
        )