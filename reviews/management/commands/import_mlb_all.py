from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Imports every MLB season"

    def add_arguments(self, parser):
        parser.add_argument(
            "--start",
            type=int,
            default=1901,
            help="First season to import"
        )

        parser.add_argument(
            "--end",
            type=int,
            default=2025,
            help="Last season to import"
        )

    def handle(self, *args, **kwargs):
        start = kwargs["start"]
        end = kwargs["end"]

        for season in range(start, end + 1):
            self.stdout.write(f"\n===== Importing {season} =====")
            call_command("import_mlb_season", season)

        self.stdout.write(
            self.style.SUCCESS("\nFinished importing all seasons!")
        )