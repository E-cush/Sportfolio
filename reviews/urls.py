from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("todays-games/", views.todays_games, name="todays_games"),
    path("comment/<int:comment_id>/delete/", views.delete_comment, name="delete_comment"),
    # Game search
    path("search/", views.search, name="search"),

    # User search
    path("people/", views.user_search, name="user_search"),

    # League pages
    path("mlb/", views.mlb_games, name="mlb_games"),
    path("nba/", views.nba_games, name="nba_games"),
    path("nfl/", views.nfl_games, name="nfl_games"),
    path("nhl/", views.nhl_games, name="nhl_games"),
    path("champions-league/", views.champions_league, name="champions_league"),

    # Game pages
    path("game/<int:game_id>/", views.game_detail, name="game_detail"),
    path("game/<int:game_id>/log/", views.log_game, name="log_game"),
    path("game/<int:game_id>/edit/", views.edit_log, name="edit_log"),

path(
    "game/<int:game_id>/delete/",
    views.delete_log,
    name="delete_log",
),

    # User pages
    path("social/", views.social, name="social"),
    path("diary/", views.diary, name="diary"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/logs/", views.logged_games, name="logged_games"),
    path("profile/logs/live/", views.logged_games, {"watch_type": "LIVE"}, name="live_games"),
    path("profile/logs/tv/", views.logged_games, {"watch_type": "TV"}, name="tv_games"),
    path("profile/logs/replay/", views.logged_games, {"watch_type": "REPLAY"}, name="replay_games"),
    path("profile/logs/highlights/", views.logged_games, {"watch_type": "HIGHLIGHTS"}, name="highlights_games"),
path(
    "profile/<str:username>/logs/",
    views.logged_games,
    name="user_logged_games",
),

path(
    "profile/<str:username>/logs/live/",
    views.logged_games,
    {"watch_type": "LIVE"},
    name="user_live_games",
),

path(
    "profile/<str:username>/logs/tv/",
    views.logged_games,
    {"watch_type": "TV"},
    name="user_tv_games",
),

path(
    "profile/<str:username>/logs/replay/",
    views.logged_games,
    {"watch_type": "REPLAY"},
    name="user_replay_games",
),

path(
    "profile/<str:username>/logs/highlights/",
    views.logged_games,
    {"watch_type": "HIGHLIGHTS"},
    name="user_highlights_games",
),
    path("profile/stadiums/", views.stadiums, name="stadiums"),
path(
    "profile/<str:username>/stadiums/",
    views.stadiums,
    name="user_stadiums",
),
    path("profile/<str:username>/", views.public_profile, name="public_profile"),
    path("profile/<str:username>/follow/", views.follow_user, name="follow_user"),

path(
    "profile/<str:username>/followers/",
    views.followers_list,
    name="followers_list",
),

path(
    "profile/<str:username>/following/",
    views.following_list,
    name="following_list",
),

    path(
        "profile/<str:username>/following/",
        views.following_list,
        name="following_list",
    ),

    path(
        "stats/",
        views.stats,
        name="stats",
    ),

path(
    "profile/<str:username>/stats/",
    views.user_stats,
    name="user_stats",
),

    # Miscellaneous
    path(
        "coming-soon/",
        views.coming_soon,
        name="coming_soon",
    ),

path(
    "game/<int:game_id>/remove-log/",
    views.remove_log,
    name="remove_log",
),

path("privacy/", views.privacy_policy, name="privacy_policy"),

path("support/", views.support, name="support"),

path(
    "delete-account/",
    views.delete_account,
    name="delete_account",
),
]