import os
import re
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Load .env
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("THESPORTSDB_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "THESPORTSDB_API_KEY was not found in .env"
    )

API_BASE = (
    f"https://www.thesportsdb.com/api/v1/json/{API_KEY}"
)

OUTPUT_BASE = BASE_DIR / "static" / "logos" / "tsdb"


# ==========================================================
# SPORTFOLIO TEAMS
# ==========================================================

TEAMS = {
    "mlb": {
        "Arizona Diamondbacks": "arizona-diamondbacks",
        "Athletics": "athletics",
        "Atlanta Braves": "atlanta-braves",
        "Baltimore Orioles": "baltimore-orioles",
        "Boston Red Sox": "boston-red-sox",
        "Chicago Cubs": "chicago-cubs",
        "Chicago White Sox": "chicago-white-sox",
        "Cincinnati Reds": "cincinnati-reds",
        "Cleveland Guardians": "cleveland-guardians",
        "Colorado Rockies": "colorado-rockies",
        "Detroit Tigers": "detroit-tigers",
        "Houston Astros": "houston-astros",
        "Kansas City Royals": "kansas-city-royals",
        "Los Angeles Angels": "los-angeles-angels",
        "Los Angeles Dodgers": "los-angeles-dodgers",
        "Miami Marlins": "miami-marlins",
        "Milwaukee Brewers": "milwaukee-brewers",
        "Minnesota Twins": "minnesota-twins",
        "New York Mets": "new-york-mets",
        "New York Yankees": "new-york-yankees",
        "Philadelphia Phillies": "philadelphia-phillies",
        "Pittsburgh Pirates": "pittsburgh-pirates",
        "San Diego Padres": "san-diego-padres",
        "San Francisco Giants": "san-francisco-giants",
        "Seattle Mariners": "seattle-mariners",
        "St. Louis Cardinals": "st-louis-cardinals",
        "Tampa Bay Rays": "tampa-bay-rays",
        "Texas Rangers": "texas-rangers",
        "Toronto Blue Jays": "toronto-blue-jays",
        "Washington Nationals": "washington-nationals",
    },

    "nba": {
        "Atlanta Hawks": "atlanta-hawks",
        "Boston Celtics": "boston-celtics",
        "Brooklyn Nets": "brooklyn-nets",
        "Charlotte Hornets": "charlotte-hornets",
        "Chicago Bulls": "chicago-bulls",
        "Cleveland Cavaliers": "cleveland-cavaliers",
        "Dallas Mavericks": "dallas-mavericks",
        "Denver Nuggets": "denver-nuggets",
        "Detroit Pistons": "detroit-pistons",
        "Golden State Warriors": "golden-state-warriors",
        "Houston Rockets": "houston-rockets",
        "Indiana Pacers": "indiana-pacers",
        "Los Angeles Clippers": "los-angeles-clippers",
        "Los Angeles Lakers": "los-angeles-lakers",
        "Memphis Grizzlies": "memphis-grizzlies",
        "Miami Heat": "miami-heat",
        "Milwaukee Bucks": "milwaukee-bucks",
        "Minnesota Timberwolves": "minnesota-timberwolves",
        "New Orleans Pelicans": "new-orleans-pelicans",
        "New York Knicks": "new-york-knicks",
        "Oklahoma City Thunder": "oklahoma-city-thunder",
        "Orlando Magic": "orlando-magic",
        "Philadelphia 76ers": "philadelphia-76ers",
        "Phoenix Suns": "phoenix-suns",
        "Portland Trail Blazers": "portland-trail-blazers",
        "Sacramento Kings": "sacramento-kings",
        "San Antonio Spurs": "san-antonio-spurs",
        "Toronto Raptors": "toronto-raptors",
        "Utah Jazz": "utah-jazz",
        "Washington Wizards": "washington-wizards",
    },

    "nfl": {
        "Arizona Cardinals": "arizona-cardinals",
        "Atlanta Falcons": "atlanta-falcons",
        "Baltimore Ravens": "baltimore-ravens",
        "Buffalo Bills": "buffalo-bills",
        "Carolina Panthers": "carolina-panthers",
        "Chicago Bears": "chicago-bears",
        "Cincinnati Bengals": "cincinnati-bengals",
        "Cleveland Browns": "cleveland-browns",
        "Dallas Cowboys": "dallas-cowboys",
        "Denver Broncos": "denver-broncos",
        "Detroit Lions": "detroit-lions",
        "Green Bay Packers": "green-bay-packers",
        "Houston Texans": "houston-texans",
        "Indianapolis Colts": "indianapolis-colts",
        "Jacksonville Jaguars": "jacksonville-jaguars",
        "Kansas City Chiefs": "kansas-city-chiefs",
        "Las Vegas Raiders": "las-vegas-raiders",
        "Los Angeles Chargers": "los-angeles-chargers",
        "Los Angeles Rams": "los-angeles-rams",
        "Miami Dolphins": "miami-dolphins",
        "Minnesota Vikings": "minnesota-vikings",
        "New England Patriots": "new-england-patriots",
        "New Orleans Saints": "new-orleans-saints",
        "New York Giants": "new-york-giants",
        "New York Jets": "new-york-jets",
        "Philadelphia Eagles": "philadelphia-eagles",
        "Pittsburgh Steelers": "pittsburgh-steelers",
        "San Francisco 49ers": "san-francisco-49ers",
        "Seattle Seahawks": "seattle-seahawks",
        "Tampa Bay Buccaneers": "tampa-bay-buccaneers",
        "Tennessee Titans": "tennessee-titans",
        "Washington Commanders": "washington-commanders",
    },

    "nhl": {
        "Anaheim Ducks": "anaheim-ducks",
        "Boston Bruins": "boston-bruins",
        "Buffalo Sabres": "buffalo-sabres",
        "Calgary Flames": "calgary-flames",
        "Carolina Hurricanes": "carolina-hurricanes",
        "Chicago Blackhawks": "chicago-blackhawks",
        "Colorado Avalanche": "colorado-avalanche",
        "Columbus Blue Jackets": "columbus-blue-jackets",
        "Dallas Stars": "dallas-stars",
        "Detroit Red Wings": "detroit-red-wings",
        "Edmonton Oilers": "edmonton-oilers",
        "Florida Panthers": "florida-panthers",
        "Los Angeles Kings": "los-angeles-kings",
        "Minnesota Wild": "minnesota-wild",
        "Montreal Canadiens": "montreal-canadiens",
        "Nashville Predators": "nashville-predators",
        "New Jersey Devils": "new-jersey-devils",
        "New York Islanders": "new-york-islanders",
        "New York Rangers": "new-york-rangers",
        "Ottawa Senators": "ottawa-senators",
        "Philadelphia Flyers": "philadelphia-flyers",
        "Pittsburgh Penguins": "pittsburgh-penguins",
        "San Jose Sharks": "san-jose-sharks",
        "Seattle Kraken": "seattle-kraken",
        "St. Louis Blues": "st-louis-blues",
        "Tampa Bay Lightning": "tampa-bay-lightning",
        "Toronto Maple Leafs": "toronto-maple-leafs",
        "Utah Mammoth": "utah-mammoth",
        "Vancouver Canucks": "vancouver-canucks",
        "Vegas Golden Knights": "vegas-golden-knights",
        "Washington Capitals": "washington-capitals",
        "Winnipeg Jets": "winnipeg-jets",
    },

    "PL": {
        "Arsenal": "arsenal",
        "AFC Bournemouth": "bournemouth",
        "Aston Villa": "aston-villa",
        "Brentford": "brentford",
        "Brighton & Hove Albion": "brighton",
        "Chelsea": "chelsea",
        "Coventry City": "coventry-city",
        "Crystal Palace": "crystal-palace",
        "Everton": "everton",
        "Fulham": "fulham",
        "Hull City": "hull-city",
        "Ipswich Town": "ipswich-town",
        "Leeds United": "leeds-united",
        "Liverpool": "liverpool",
        "Manchester City": "manchester-city",
        "Manchester United": "manchester-united",
        "Newcastle United": "newcastle-united",
        "Nottingham Forest": "nottingham-forest",
        "Sunderland": "sunderland",
        "Tottenham Hotspur": "tottenham-hotspur",
    },

    "laliga": {
        "Athletic Club": "athletic-club",
        "Atletico Madrid": "atletico-madrid",
        "CA Osasuna": "osasuna",
        "Celta Vigo": "celta-vigo",
        "Deportivo Alaves": "alaves",
        "Elche CF": "elche",
        "FC Barcelona": "barcelona",
        "Getafe CF": "getafe",
        "Levante UD": "levante",
        "Malaga CF": "malaga",
        "Racing Santander": "racing-santander",
        "Rayo Vallecano": "rayo-vallecano",
        "Deportivo La Coruna": "deportivo",
        "Espanyol": "espanyol",
        "Real Betis": "real-betis",
        "Real Madrid": "real-madrid",
        "Real Sociedad": "real-sociedad",
        "Sevilla FC": "sevilla",
        "Valencia CF": "valencia",
        "Villarreal CF": "villarreal",
    },
}


# ==========================================================
# HELPERS
# ==========================================================

LEAGUE_SEARCH_NAMES = {
    "mlb": "MLB",
    "nba": "NBA",
    "nfl": "NFL",
    "nhl": "NHL",
    "PL": "English Premier League",
    "laliga": "La Liga",
}

def search_team(team_name, expected_league):
    """Find a team and make sure it belongs to the expected league."""

    url = f"{API_BASE}/searchteams.php"

    response = requests.get(
        url,
        params={"t": team_name},
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()
    teams = data.get("teams") or []

    expected_name = LEAGUE_SEARCH_NAMES.get(
        expected_league,
        expected_league,
    ).lower()

    for team in teams:
        league = (team.get("strLeague") or "").lower()

        if expected_name in league:
            return team

        # Some former Premier League clubs are currently listed
        # in the Championship but still need their club badge.
    if expected_league == "PL":
        for team in teams:
            if team.get("strTeam") in {
                "Burnley",
                "West Ham United",
                "Wolverhampton Wanderers",
            }:
                return team

    return None


def download_team_badge(team_name, filename, league):
    """Download a team's TheSportsDB badge."""

    team = search_team(team_name, league)

    if not team:
        print(
            f"✗ {league.upper()} | {team_name} "
            f"— team not found"
        )
        return False

    badge_url = team.get("strBadge")

    if not badge_url:
        print(
            f"✗ {league.upper()} | {team_name} "
            f"— no badge"
        )
        return False

    response = requests.get(
        badge_url,
        timeout=20,
    )

    if response.status_code != 200:
        print(
            f"✗ {league.upper()} | {team_name} "
            f"— image HTTP {response.status_code}"
        )
        return False

    output_dir = OUTPUT_BASE / league
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = output_dir / f"{filename}.png"

    with open(output_file, "wb") as f:
        f.write(response.content)

    print(
        f"✓ {league.upper()} | {team_name}"
        f" → {output_file.name}"
    )

    return True


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    print("\nDownloading Sportfolio logos from TheSportsDB...\n")

    successful = 0
    failed = 0

    for league, teams in TEAMS.items():

        if league not in ["PL", "laliga"]:
            continue

        print(f"\n===== {league.upper()} =====")

        for team_name, filename in teams.items():

            try:
                if download_team_badge(
                    team_name,
                    filename,
                    league,
                ):
                    successful += 1
                else:
                    failed += 1

            except Exception as e:
                print(
                    f"✗ {league.upper()} | {team_name}"
                    f" — {e}"
                )
                failed += 1

            # Stay comfortably below the API rate limit.
            time.sleep(3)

    print("\n================================")
    print("Download complete.")
    print(f"Successful: {successful}")
    print(f"Failed:     {failed}")
    print("================================\n")