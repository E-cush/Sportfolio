import re
import requests
from datetime import datetime

BASE_URL = (
    "https://raw.githubusercontent.com/"
    "openfootball/champions-league/master"
)


def download_season(season):
    url = f"{BASE_URL}/{season}/cl.txt"

    response = requests.get(url)
    response.raise_for_status()

    return response.text


def parse_season(text):
    import re

    matches = []

    current_date = None
    current_stage = ""

    for line in text.splitlines():

        line = line.rstrip()

        if not line:
            continue

        # Stage
        if line.startswith("= "):
            current_stage = line.replace("=", "").strip()
            continue

        # Date
        try:
            current_date = datetime.strptime(
                line.strip(),
                "%a %b %d %Y"
            ).date()
            continue
        except ValueError:
            pass

        # Remove optional kickoff time
        line = re.sub(r"^\s*\d{1,2}:\d{2}\s+", "", line)

        # Match line
        match = re.search(
            r"(.+?)\s+\([A-Z]{3}\)\s+v\s+(.+?)\s+\([A-Z]{3}\)\s+(\d+)-(\d+)",
            line,
        )

        if not match:
            continue

        matches.append({
            "date": current_date,
            "stage": current_stage,
            "home_team": match.group(1).strip(),
            "away_team": match.group(2).strip(),
            "home_score": int(match.group(3)),
            "away_score": int(match.group(4)),
        })

    return matches

if __name__ == "__main__":
    text = download_season("2024-25")
    matches = parse_season(text)
    print(len(matches))