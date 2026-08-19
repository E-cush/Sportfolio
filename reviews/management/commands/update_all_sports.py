from datetime import timedelta
from django.utils import timezone

from django.core.management.base import BaseCommand

from reviews.updates.mlb import update_mlb
from reviews.updates.nba import update_nba
from reviews.updates.nfl import update_nfl
from reviews.updates.nhl import update_nhl


class Command(BaseCommand):
    help = "Updates games for one day or a date range"

    def add_arguments(self, parser):
        parser.add_argument(
            "start_date",
            nargs="?",
            default=date.today().isoformat(),
            help="Start date (YYYY-MM-DD)",
        )

        parser.add_argument(
            "end_date",
            nargs="?",
            help="End date (YYYY-MM-DD)",
        )

    def handle(self, *args, **kwargs):

        if kwargs["end_date"]:
            start_date = kwargs["start_date"]
            end_date = kwargs["end_date"]
        else:
            today = timezone.localdate()
            start_date = (today - timedelta(days=1)).isoformat()
            end_date = (today + timedelta(days=1)).isoformat()

        self.stdout.write("")
        self.stdout.write("=" * 40)
        self.stdout.write("Sportfolio Game Updater")
        self.stdout.write("=" * 40)
        self.stdout.write(f"Updating games from {start_date} to {end_date}")
        self.stdout.write("")

        update_mlb(start_date, end_date)
        update_nba(start_date, end_date)
        update_nfl(start_date, end_date)
        update_nhl(start_date, end_date)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("Finished updating all sports.")
        )