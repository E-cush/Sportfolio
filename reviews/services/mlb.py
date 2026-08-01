import statsapi


def get_linescore(game_id):
    try:
        data = statsapi.get(
            "game",
            {
                "gamePk": game_id,
            },
        )

        teams = data["liveData"]["linescore"]["teams"]

        return {
            "home": teams["home"],
            "away": teams["away"],
        }

    except Exception as e:
        print(e)
        return None