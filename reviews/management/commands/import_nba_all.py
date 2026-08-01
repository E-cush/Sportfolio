from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command


class Command(BaseCommand):
    help = "Imports multiple NBA seasons"

    def add_arguments(self, parser):
        parser.add_argument(
            "--start",
            type=int,
            default=1947,
            help="First season to import (default: 1947)"
        )

        parser.add_argument(
            "--end",
            type=int,
            default=2025,
            help="Last season to import (default: 2025)"
        )

    def handle(self, *args, **kwargs):
        start = kwargs["start"]
        end = kwargs["end"]

        if start > end:
            raise CommandError("Start season cannot be greater than end season.")

        for season in range(start, end + 1):
            self.stdout.write(
                self.style.NOTICE(
                    f"\n========== {season}-{season + 1} =========="
                )
            )

            call_command("import_nba_season", season)

        self.stdout.write(
            self.style.SUCCESS(
                "\nFinished importing all requested NBA seasons!"
            )
        )