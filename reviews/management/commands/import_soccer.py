from datetime import datetime

from django.core.management.base import BaseCommand

from reviews.models import Game
from reviews.openfootball import download_season, parse_season







class Command(BaseCommand):
    help = "Import soccer matches from football-data.org"

    def add_arguments(self, parser):
        parser.add_argument(
            "competition",
            type=str,
            help="Competition code (CL, PL, PD, BL1, SA, MLS)",
        )

        parser.add_argument(
            "season",
            nargs="?",
            default="all",
            help='Season year (example: 2025) or "all"',
        )

    def handle(self, *args, **options):
        competition = options["competition"]
        season = options["season"]

        headers = {
            "X-Auth-Token": settings.FOOTBALL_DATA_API_KEY,
        }

        if season == "all":

            response = requests.get(
                f"{BASE_URL}/competitions/{competition}",
                headers=headers,
            )

            response.raise_for_status()

            competition_data = response.json()

            seasons = competition_data["seasons"]

            seasons = sorted(
                seasons,
                key=lambda s: s["startDate"]
            )

            total_matches = 0

            for season_info in seasons:

                start_year = int(season_info["startDate"][:4])

                if start_year < 1980:
                    continue

                self.stdout.write(
                    self.style.WARNING(
                        f"\nImporting {start_year}-{start_year + 1}..."
                    )
                )

                season_string = f"{season}-{str(season + 1)[2:]}"

                text = download_season(season_string)

                matches = parse_season(text)

                competition_name = "UEFA Champions League"

                for match in matches:

                    Game.objects.update_or_create(
                        game_id=match["id"],
                        defaults={
                            "league": "Soccer",
                            "competition": competition_name,
                            "season": start_year,
                            "game_type": match["stage"],
                            "home_team": match["homeTeam"]["name"],
                            "away_team": match["awayTeam"]["name"],
                            "game_date": datetime.fromisoformat(
                                match["utcDate"].replace("Z", "+00:00")
                            ).date(),
                            "home_score": match["score"]["fullTime"]["home"] or 0,
                            "away_score": match["score"]["fullTime"]["away"] or 0,
                            "venue": "",
                            "status": match["status"],
                        },
                    )

                total_matches += len(matches)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Imported {len(matches)} matches."
                    )
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"\nFinished! Imported {total_matches} total matches."
                )
            )

        else:

            season = int(season)

            self.stdout.write(
                f"Importing {competition} ({season})..."
            )

            data = get_matches(competition, season)

            matches = data["matches"]

            competition_name = data["competition"]["name"]

            for match in matches:

                Game.objects.update_or_create(
                    game_id=match["id"],
                    defaults={
                        "league": "Soccer",
                        "competition": competition_name,
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

            self.stdout.write(
                self.style.SUCCESS(
                    f"Imported {len(matches)} matches."
                )
            )