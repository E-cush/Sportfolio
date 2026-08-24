import requests
from datetime import datetime

from reviews.models import Game


ESPN_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/"
    "soccer/eng.1/scoreboard"
)


def update_PL(start_date, end_date):
    params = {
        "limit": 1000,
        "dates": (
            f"{start_date.replace('-', '')}-"
            f"{end_date.replace('-', '')}"
        ),
    }

    try:
        response = requests.get(
            ESPN_URL,
            params=params,
            timeout=20,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Premier League update failed: {e}")
        return

    events = response.json().get("events", [])

    created = 0
    updated = 0

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

            venue = competition.get(
                "venue",
                {}
            ).get(
                "fullName",
                ""
            )

            season_year = event.get(
                "season",
                {}
            ).get(
                "year",
                event_date.year
            )

            _, was_created = Game.objects.update_or_create(
                game_id=event_id,
                defaults={
                    "status": status,
                    "league": "Soccer",
                    "competition": "English Premier League",
                    "season": season_year,
                    "game_type": "Regular Season",
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
            else:
                updated += 1

        except (
            KeyError,
            ValueError,
            StopIteration,
        ):
            continue

    print(
        f"Premier League: "
        f"{created} created, {updated} updated"
    )