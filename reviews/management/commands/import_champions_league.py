from django.core.management.base import BaseCommand

from reviews.models import Game
from reviews.openfootball import download_season, parse_season


class Command(BaseCommand):
    help = "Import UEFA Champions League matches from OpenFootball"

    def add_arguments(self, parser):
        parser.add_argument(
            "season",
            nargs="?",
            default="all",
            help='Season year (example: 2024) or "all"',
        )

    def handle(self, *args, **options):

        season = options["season"]

        if season == "all":

            imported_total = 0

            # OpenFootball Champions League repository begins with the 2011-12 season.
            for start_year in range(2011, 2026):

                season_string = f"{start_year}-{str(start_year + 1)[2:]}"

                self.stdout.write(
                    self.style.WARNING(
                        f"Importing {season_string}..."
                    )
                )

                try:

                    text = download_season(season_string)


                except Exception as e:

                    self.stdout.write(

                        self.style.ERROR(

                            f"Skipped {season_string}: {e}"

                        )

                    )

                    continue

                matches = parse_season(text)

                for i, match in enumerate(matches):
                    game_id = int(f"{start_year}{i:03}")

                    Game.objects.update_or_create(
                        game_id=game_id,
                        defaults={
                            "league": "Soccer",
                            "competition": "UEFA Champions League",
                            "season": start_year,
                            "game_type": match["stage"],
                            "home_team": match["home_team"],
                            "away_team": match["away_team"],
                            "game_date": match["date"],
                            "home_score": match["home_score"],
                            "away_score": match["away_score"],
                            "venue": "",
                            "status": "FINISHED",
                        },
                    )

                imported_total += len(matches)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Imported {len(matches)} matches."
                    )
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"\nFinished! Imported {imported_total} matches."
                )
            )

        else:

            season = int(season)

            season_string = f"{season}-{str(season + 1)[2:]}"

            text = download_season(season_string)

            matches = parse_season(text)

            imported = 0

            for i, match in enumerate(matches):
                game_id = int(f"{season}{i:03}")

                Game.objects.update_or_create(
                    game_id=game_id,
                    defaults={
                        "league": "Soccer",
                        "competition": "UEFA Champions League",
                        "season": season,
                        "game_type": match["stage"],
                        "home_team": match["home_team"],
                        "away_team": match["away_team"],
                        "game_date": match["date"],
                        "home_score": match["home_score"],
                        "away_score": match["away_score"],
                        "venue": "",
                        "status": "FINISHED",
                    },
                )

                imported += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Imported {imported} Champions League matches."
                )
            )