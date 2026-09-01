from datetime import datetime

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Import historical Formula 1 and NASCAR Cup Series races"

    def add_arguments(self, parser):

        parser.add_argument(
            "--f1-start",
            type=int,
            default=1950,
            help="First Formula 1 season to import",
        )

        parser.add_argument(
            "--nascar-start",
            type=int,
            default=2011,
            help="First NASCAR Cup season to import",
        )

        parser.add_argument(
            "--end",
            type=int,
            default=datetime.now().year,
            help="Last season to import",
        )

    def handle(self, *args, **options):

        f1_start = options["f1_start"]
        nascar_start = options["nascar_start"]
        end_year = options["end"]

        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write("SPORTFOLIO RACING HISTORY IMPORT")
        self.stdout.write("=" * 50)

        # =========================================
        # FORMULA 1
        # =========================================

        self.stdout.write("")
        self.stdout.write(
            f"Importing Formula 1: "
            f"{f1_start}-{end_year}"
        )

        for season in range(
            f1_start,
            end_year + 1,
        ):

            self.stdout.write("")
            self.stdout.write(
                f"--- F1 {season} ---"
            )

            try:
                call_command(
                    "import_f1",
                    season,
                )

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"F1 {season} failed: {e}"
                    )
                )

        # =========================================
        # NASCAR CUP SERIES
        # =========================================

        self.stdout.write("")
        self.stdout.write(
            f"Importing NASCAR Cup Series: "
            f"{nascar_start}-{end_year}"
        )

        for season in range(
            nascar_start,
            end_year + 1,
        ):

            self.stdout.write("")
            self.stdout.write(
                f"--- NASCAR {season} ---"
            )

            try:
                call_command(
                    "import_nascar",
                    season,
                )

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"NASCAR {season} failed: {e}"
                    )
                )

        # =========================================
        # FINISHED
        # =========================================

        self.stdout.write("")
        self.stdout.write("=" * 50)

        self.stdout.write(
            self.style.SUCCESS(
                "Racing history import complete."
            )
        )

        self.stdout.write("=" * 50)