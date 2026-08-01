import statsapi

from reviews.models import Game


def update_mlb(start_date, end_date):
    print(f"Updating MLB ({start_date} → {end_date})...")

    try:
        games = statsapi.schedule(
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as e:
        print(f"Failed to retrieve MLB schedule: {e}")
        return

    updated = 0

    for game in games:

        rows = Game.objects.filter(
            game_id=game["game_id"],
            league="MLB",
        ).update(
            status=game["status"],
            home_score=game["home_score"],
            away_score=game["away_score"],
            venue=game.get("venue_name") or "Unknown Venue",
        )

        updated += rows

    print(f"Updated {updated} MLB games.")