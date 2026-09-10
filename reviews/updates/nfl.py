import hashlib
import requests
import pandas as pd

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from reviews.models import Game


EASTERN = ZoneInfo("America/New_York")


def stable_game_id(source_game_id):
    digest = hashlib.sha256(
        str(source_game_id).encode("utf-8")
    ).digest()

    return int.from_bytes(
        digest[:8],
        byteorder="big",
        signed=False,
    ) & 0x7FFFFFFFFFFFFFFF


def normalize_nfl_team(team):
    """
    Make ESPN abbreviations match the abbreviations
    already stored in Sportfolio.
    """

    aliases = {
        "WSH": "WAS",
        "JAC": "JAX",
        "LA": "LAR",
    }

    team = (team or "").upper()

    return aliases.get(team, team)


def update_nfl(start_date, end_date):
    print(f"Updating NFL ({start_date} → {end_date})...")

    updated_game_ids = set()

    # ============================================================
    # NFLVERSE — SCHEDULE / KICKOFF TIMES
    # ============================================================

    try:
        df = pd.read_csv(
            "https://github.com/nflverse/nfldata/raw/master/data/games.csv"
        )

    except Exception as e:
        print(f"Failed to retrieve NFL schedule: {e}")
        df = pd.DataFrame()

    if not df.empty:

        df = df[
            (df["season"] == 2026) &
            (df["game_type"] != "PRE") &
            (df["gameday"] >= start_date) &
            (df["gameday"] <= end_date)
        ]

        for _, game in df.iterrows():

            game_type = {
                "REG": "Regular Season",
                "WC": "Wild Card",
                "DIV": "Divisional",
                "CON": "Conference Championship",
                "SB": "Super Bowl",
            }.get(
                game["game_type"],
                game["game_type"],
            )

            home_score = (
                0
                if pd.isna(game["home_score"])
                else int(game["home_score"])
            )

            away_score = (
                0
                if pd.isna(game["away_score"])
                else int(game["away_score"])
            )

            status = (
                "Scheduled"
                if pd.isna(game["home_score"])
                else "Final"
            )

            # ====================================================
            # KICKOFF TIME
            # NFLVerse gametime is Eastern Time
            # ====================================================

            game_start = None

            gameday = game.get("gameday")
            gametime = game.get("gametime")

            if (
                not pd.isna(gameday)
                and not pd.isna(gametime)
            ):
                try:

                    kickoff_string = (
                        f"{gameday} {gametime}"
                    )

                    game_start = datetime.strptime(
                        kickoff_string,
                        "%Y-%m-%d %H:%M",
                    )

                    game_start = game_start.replace(
                        tzinfo=EASTERN
                    )

                except (ValueError, TypeError):
                    game_start = None

            game_id = stable_game_id(
                game["game_id"]
            )

            queryset = Game.objects.filter(
                game_id=game_id,
                league="NFL",
            )

            ids = list(
                queryset.values_list(
                    "id",
                    flat=True,
                )
            )

            queryset.update(
                status=status,
                home_score=home_score,
                away_score=away_score,
                venue=(
                    ""
                    if pd.isna(game["stadium"])
                    else game["stadium"]
                ),
                game_type=game_type,
                game_date=game["gameday"],
                game_start=game_start,
            )

            updated_game_ids.update(ids)

    # ============================================================
    # ESPN — LIVE SCORES / STATUS / PRESEASON / PLAYOFFS
    #
    # This section runs AFTER NFLVerse so ESPN gets the final say
    # on live score and live status.
    # ============================================================

    espn_url = (
        "https://site.api.espn.com/apis/site/v2/sports/"
        "football/nfl/scoreboard"
    )

    start_date_obj = pd.to_datetime(
        start_date
    ).date()

    end_date_obj = pd.to_datetime(
        end_date
    ).date()

    current_date = start_date_obj

    while current_date <= end_date_obj:

        try:

            response = requests.get(
                espn_url,
                params={
                    "dates": current_date.strftime(
                        "%Y%m%d"
                    ),
                    "limit": 100,
                },
                timeout=30,
            )

            response.raise_for_status()

            data = response.json()

        except Exception as e:

            print(
                f"Failed to retrieve ESPN NFL data "
                f"for {current_date}: {e}"
            )

            current_date += timedelta(days=1)
            continue

        events = data.get("events", [])

        for event in events:

            competitions = event.get(
                "competitions",
                [],
            )

            if not competitions:
                continue

            competition = competitions[0]

            home_team = None
            away_team = None

            home_score = 0
            away_score = 0

            # ====================================================
            # TEAMS + LIVE SCORES
            # ====================================================

            for competitor in competition.get(
                "competitors",
                [],
            ):

                team_data = competitor.get(
                    "team",
                    {},
                )

                team = normalize_nfl_team(
                    team_data.get(
                        "abbreviation",
                        "",
                    )
                )

                score = competitor.get(
                    "score",
                    0,
                )

                try:
                    score = int(score)
                except (TypeError, ValueError):
                    score = 0

                if competitor.get(
                    "homeAway"
                ) == "home":

                    home_team = team
                    home_score = score

                elif competitor.get(
                    "homeAway"
                ) == "away":

                    away_team = team
                    away_score = score

            if not home_team or not away_team:
                continue

            # ====================================================
            # GAME START + EASTERN DATE
            # ====================================================

            game_start = None
            game_date = current_date

            event_date = event.get("date")

            if event_date:

                try:

                    game_start = datetime.fromisoformat(
                        event_date.replace(
                            "Z",
                            "+00:00",
                        )
                    )

                    game_start = (
                        game_start.astimezone(
                            EASTERN
                        )
                    )

                    game_date = game_start.date()

                except (
                    ValueError,
                    TypeError,
                ):
                    game_start = None

            if (
                game_date < start_date_obj
                or game_date > end_date_obj
            ):
                continue

            # ====================================================
            # ESPN LIVE STATUS
            # ====================================================

            status_type = (
                competition
                .get("status", {})
                .get("type", {})
            )

            completed = status_type.get(
                "completed",
                False,
            )

            state = str(
                status_type.get(
                    "state",
                    "",
                )
            ).lower()

            detail = (
                status_type.get("shortDetail")
                or status_type.get("detail")
                or ""
            )

            if completed:
                status = "Final"

            elif state == "in":
                status = (
                    detail
                    if detail
                    else "In Progress"
                )

            else:
                status = "Scheduled"

            # ====================================================
            # VENUE
            # ====================================================

            venue = (
                competition
                .get("venue", {})
                .get("fullName", "")
            )

            # ====================================================
            # FIND EXISTING SPORTFOLIO GAME
            #
            # Regular-season games use NFLVerse IDs,
            # while ESPN has its own IDs.
            #
            # Matching by date + teams lets ESPN update the
            # SAME database record rather than creating duplicates.
            # ====================================================

            queryset = Game.objects.filter(
                league="NFL",
                game_date=game_date,
                home_team=home_team,
                away_team=away_team,
            )

            # ----------------------------------------------------
            # Preseason fallback
            # Existing preseason games may use ESPN_PRE IDs.
            # ----------------------------------------------------

            if not queryset.exists():

                espn_pre_id = stable_game_id(
                    f"ESPN_PRE_{event.get('id')}"
                )

                queryset = Game.objects.filter(
                    league="NFL",
                    game_id=espn_pre_id,
                )

            ids = list(
                queryset.values_list(
                    "id",
                    flat=True,
                )
            )

            if not ids:
                continue

            queryset.update(
                status=status,
                home_score=home_score,
                away_score=away_score,
                venue=venue,
                game_start=game_start,
            )

            updated_game_ids.update(ids)

        current_date += timedelta(days=1)

    print(
        f"Updated "
        f"{len(updated_game_ids)} "
        f"NFL games."
    )