import requests

from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from reviews.models import Game


ESPN_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/"
    "football/college-football/scoreboard"
)


class Command(BaseCommand):
    help = "Import college football games from ESPN"

    def add_arguments(self, parser):
        parser.add_argument("--start-date")
        parser.add_argument("--end-date")

    def handle(self, *args, **options):
        start_date = options.get("start_date")
        end_date = options.get("end_date")

        if start_date and end_date:
            date_range = f"{start_date}-{end_date}"
        else:
            today = datetime.now().strftime("%Y%m%d")
            end_of_season = f"{datetime.now().year}1231"
            date_range = f"{today}-{end_of_season}"

        params = {
            "groups": 80,
            "limit": 1000,
            "dates": date_range,
        }

        self.stdout.write("Fetching college football games from ESPN...")

        try:
            response = requests.get(
                ESPN_URL,
                params=params,
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f"ESPN request failed: {e}")
            )
            return

        data = response.json()
        events = data.get("events", [])

        self.stdout.write(
            f"Found {len(events)} college football games."
        )

        created = 0
        updated = 0
        skipped = 0

        for event in events:
            try:
                event_id = int(event["id"])
                event_date = datetime.fromisoformat(
                    event["date"].replace("Z", "+00:00")
                )

                competition = event["competitions"][0]

                competitors = competition["competitors"]

                home = next(
                    team for team in competitors
                    if team["homeAway"] == "home"
                )

                away = next(
                    team for team in competitors
                    if team["homeAway"] == "away"
                )

                home_team = home["team"]["displayName"]
                away_team = away["team"]["displayName"]

                home_score = int(home.get("score", 0) or 0)
                away_score = int(away.get("score", 0) or 0)

                status_data = competition["status"]["type"]

                status_name = status_data.get(
                    "name",
                    "STATUS_SCHEDULED"
                )

                if status_data.get("completed"):
                    status = "Final"
                elif status_name == "STATUS_IN_PROGRESS":
                    status = "Live"
                elif status_name == "STATUS_SCHEDULED":
                    status = "Scheduled"
                else:
                    status = status_data.get(
                        "description",
                        "Scheduled"
                    )

                venue = competition.get("venue", {}).get(
                    "fullName",
                    ""
                )

                season_data = event.get("season", {})
                season_type_data = season_data.get("type", {})

                if isinstance(season_type_data, dict):
                    season_type = season_type_data.get("name", "")
                else:
                    season_type = str(season_type_data)

                if season_type.lower() == "postseason":
                    game_type = "Playoffs"
                else:
                    game_type = "Regular Season"

                game, was_created = Game.objects.update_or_create(
                    game_id=event_id,
                    defaults={
                        "status": status,
                        "league": "NCAA",
                        "competition": "College Football",
                        "season": event_date.year,
                        "game_type": game_type,
                        "home_team": home_team,
                        "away_team": away_team,
                        "game_date": event_date.date(),
                        "home_score": home_score,
                        "away_score": away_score,
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
                    f"{away_team} @ {home_team} "
                    f"({event_date.date()})"
                )

            except (KeyError, ValueError, StopIteration) as e:
                skipped += 1

                self.stdout.write(
                    self.style.WARNING(
                        f"Skipped event {event.get('id', 'UNKNOWN')}: {e}"
                    )
                )

            except IntegrityError as e:
                skipped += 1

                self.stdout.write(
                    self.style.WARNING(
                        f"Database error for event "
                        f"{event.get('id', 'UNKNOWN')}: {e}"
                    )
                )

        self.stdout.write("")
        self.stdout.write("=" * 40)
        self.stdout.write("College football import complete.")
        self.stdout.write(f"Created: {created}")
        self.stdout.write(f"Updated: {updated}")
        self.stdout.write(f"Skipped: {skipped}")
        self.stdout.write("=" * 40)