import os
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================
# MLB
# ==========================================

MLB_OUTPUT = os.path.join(BASE_DIR, "static", "logos", "mlb")
os.makedirs(MLB_OUTPUT, exist_ok=True)

MLB_TEAM_IDS = {
    "arizona-diamondbacks": 109,
    "athletics": 133,
    "atlanta-braves": 144,
    "baltimore-orioles": 110,
    "boston-red-sox": 111,
    "chicago-cubs": 112,
    "chicago-white-sox": 145,
    "cincinnati-reds": 113,
    "cleveland-guardians": 114,
    "colorado-rockies": 115,
    "detroit-tigers": 116,
    "houston-astros": 117,
    "kansas-city-royals": 118,
    "los-angeles-angels": 108,
    "los-angeles-dodgers": 119,
    "miami-marlins": 146,
    "milwaukee-brewers": 158,
    "minnesota-twins": 142,
    "new-york-mets": 121,
    "new-york-yankees": 147,
    "philadelphia-phillies": 143,
    "pittsburgh-pirates": 134,
    "san-diego-padres": 135,
    "san-francisco-giants": 137,
    "seattle-mariners": 136,
    "st-louis-cardinals": 138,
    "tampa-bay-rays": 139,
    "texas-rangers": 140,
    "toronto-blue-jays": 141,
    "washington-nationals": 120,
}

def download_mlb():
    print("\nDownloading MLB logos...\n")

    for filename, team_id in MLB_TEAM_IDS.items():
        url = f"https://www.mlbstatic.com/team-logos/{team_id}.svg"

        response = requests.get(url, timeout=20)

        if response.status_code == 200:
            with open(os.path.join(MLB_OUTPUT, f"{filename}.svg"), "wb") as f:
                f.write(response.content)
            print(f"✓ {filename}")
        else:
            print(f"✗ {filename}")


# ==========================================
# NBA
# ==========================================

NBA_OUTPUT = os.path.join(BASE_DIR, "static", "logos", "nba")
os.makedirs(NBA_OUTPUT, exist_ok=True)

NBA_TEAM_IDS = {
    "atlanta-hawks": 1610612737,
    "boston-celtics": 1610612738,
    "brooklyn-nets": 1610612751,
    "charlotte-hornets": 1610612766,
    "chicago-bulls": 1610612741,
    "cleveland-cavaliers": 1610612739,
    "dallas-mavericks": 1610612742,
    "denver-nuggets": 1610612743,
    "detroit-pistons": 1610612765,
    "golden-state-warriors": 1610612744,
    "houston-rockets": 1610612745,
    "indiana-pacers": 1610612754,
    "los-angeles-clippers": 1610612746,
    "los-angeles-lakers": 1610612747,
    "memphis-grizzlies": 1610612763,
    "miami-heat": 1610612748,
    "milwaukee-bucks": 1610612749,
    "minnesota-timberwolves": 1610612750,
    "new-orleans-pelicans": 1610612740,
    "new-york-knicks": 1610612752,
    "oklahoma-city-thunder": 1610612760,
    "orlando-magic": 1610612753,
    "philadelphia-76ers": 1610612755,
    "phoenix-suns": 1610612756,
    "portland-trail-blazers": 1610612757,
    "sacramento-kings": 1610612758,
    "san-antonio-spurs": 1610612759,
    "toronto-raptors": 1610612761,
    "utah-jazz": 1610612762,
    "washington-wizards": 1610612764,
}

def download_nba():
    print("\nDownloading NBA logos...\n")

    for filename, team_id in NBA_TEAM_IDS.items():
        url = f"https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg"

        response = requests.get(url, timeout=20)

        if response.status_code == 200:
            with open(os.path.join(NBA_OUTPUT, f"{filename}.svg"), "wb") as f:
                f.write(response.content)
            print(f"✓ {filename}")
        else:
            print(f"✗ {filename}")

import pandas as pd

NFL_OUTPUT = os.path.join(BASE_DIR, "static", "logos", "nfl")
os.makedirs(NFL_OUTPUT, exist_ok=True)

NFL_DATA_URL = (
    "https://raw.githubusercontent.com/nflverse/nflverse-pbp/master/teams_colors_logos.csv"
)

def download_nfl():
    print("\nDownloading NFL logos...\n")

    teams = pd.read_csv(NFL_DATA_URL)

    # Only real NFL franchises
    teams = teams[teams["team_abbr"].str.len() <= 3]

    for _, row in teams.iterrows():

        filename = (
            row["team_name"]
            .lower()
            .replace(".", "")
            .replace(" ", "-")
        )

        logo_url = row["team_logo_espn"]

        response = requests.get(logo_url, timeout=20)

        if response.status_code == 200:
            with open(
                    os.path.join(NFL_OUTPUT, f"{filename}.png"),
                    "wb"
            ) as f:
                f.write(response.content)

            print(f"✓ {row['team_name']}")
        else:
            print(f"✗ {row['team_name']}")


if __name__ == "__main__":
    download_mlb()
    download_nba()
    download_nfl()