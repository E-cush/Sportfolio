import sqlite3
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from reviews.models import Game


class Command(BaseCommand):
    help = "Import Games from SQLite into PostgreSQL"

    def handle(self, *args, **options):
        sqlite_path = Path(__file__).resolve().parents[3] / "db.sqlite3"

        self.stdout.write(f"SQLite path: {sqlite_path}")
        print(sqlite_path.exists())

        conn = sqlite3.connect(sqlite_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        total = cur.execute(
            "SELECT COUNT(*) FROM reviews_game"
        ).fetchone()[0]

        self.stdout.write(f"Found {total:,} games.")

        cur.execute("""
            SELECT
                game_id,
                status,
                league,
                competition,
                season,
                game_type,
                home_team,
                away_team,
                game_date,
                home_score,
                away_score,
                venue
            FROM reviews_game
            ORDER BY id
        """)

        batch = []
        imported = 0
        batch_size = 5000

        for row in cur:
            batch.append(
                Game(
                    game_id=row["game_id"],
                    status=row["status"],
                    league=row["league"],
                    competition=row["competition"],
                    season=row["season"],
                    game_type=row["game_type"],
                    home_team=row["home_team"],
                    away_team=row["away_team"],
                    game_date=row["game_date"],
                    home_score=row["home_score"],
                    away_score=row["away_score"],
                    venue=row["venue"],
                )
            )

            if len(batch) >= batch_size:
                with transaction.atomic():
                    Game.objects.bulk_create(
                        batch,
                        batch_size=batch_size,
                        ignore_conflicts=True,
                    )

                imported += len(batch)
                self.stdout.write(
                    f"Imported {imported:,} / {total:,}"
                )
                batch.clear()

        if batch:
            with transaction.atomic():
                Game.objects.bulk_create(
                    batch,
                    batch_size=batch_size,
                    ignore_conflicts=True,
                )

            imported += len(batch)

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished importing {imported:,} games."
            )
        )

        conn.close()
