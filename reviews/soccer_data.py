import requests

from django.conf import settings


BASE_URL = "https://api.football-data.org/v4"


def get_matches(competition_code, season):
    """
    Fetch all matches for a competition and season.
    Example competition codes:
        CL  = Champions League
        PL  = Premier League
        PD  = La Liga
        BL1 = Bundesliga
        SA  = Serie A
        MLS = Major League Soccer
    """

    headers = {
        "X-Auth-Token": settings.FOOTBALL_DATA_API_KEY,
    }

    url = f"{BASE_URL}/competitions/{competition_code}/matches"

    response = requests.get(
        url,
        headers=headers,
        params={"season": season},
    )

    response.raise_for_status()

    return response.json()