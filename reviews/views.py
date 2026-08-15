from .services.mlb import get_linescore
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .team_aliases import NFL_ALIASES, MLB_ALIASES, NBA_ALIASES
from django.contrib.auth.models import User
from .models import Game, GameLog, Follow, Profile, Comment
from .forms import GameLogForm, ProfileForm
from django.db.models import Avg, Count
from django.core.paginator import Paginator
from .forms import CommentForm
from django.utils import timezone
from datetime import date, timedelta

def home(request):
    today = timezone.localdate()

    today_games = Game.objects.filter(
        game_date=today
    ).order_by("id")[:3]

    return render(request, "home.html", {
        "today_games": today_games,
    })

def todays_games(request):
    today = timezone.localdate()

    date_param = request.GET.get("date", "")

    if date_param:
        try:
            selected_date = date.fromisoformat(date_param)
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    previous_date = selected_date - timedelta(days=1)
    next_date = selected_date + timedelta(days=1)

    mlb_games = Game.objects.filter(
        league="MLB",
        game_date=selected_date
    ).order_by("id")

    nba_games = Game.objects.filter(
        league="NBA",
        game_date=selected_date
    ).order_by("id")

    nfl_games = Game.objects.filter(
        league="NFL",
        game_date=selected_date
    ).order_by("id")

    champions_league_games = Game.objects.filter(
        league="Soccer",
        competition="UEFA Champions League",
        game_date=selected_date
    ).order_by("id")

    return render(request, "todays_games.html", {
        "mlb_games": mlb_games,
        "nba_games": nba_games,
        "nfl_games": nfl_games,
        "champions_league_games": champions_league_games,
        "today": selected_date,
        "selected_date": selected_date,
        "previous_date": previous_date,
        "next_date": next_date,
    })

def coming_soon(request):
    return render(request, "coming_soon.html")



def search(request):
    query = request.GET.get("q", "")
    games = Game.objects.none()

    if query:
        if query.isdigit():
            games = Game.objects.filter(season=int(query))
        else:
            games = Game.objects.filter(
                Q(home_team__icontains=query) |
                Q(away_team__icontains=query)
            )

    paginator = Paginator(games, 100)   # 100 results per page
    page_number = request.GET.get("page")
    games = paginator.get_page(page_number)

    return render(request, "search.html", {
        "games": games,
        "query": query,
    })


def mlb_games(request):
    team = request.GET.get("team", "")
    opponent = request.GET.get("opponent", "")
    team_search = MLB_ALIASES.get(team.lower(), team) if team else ""
    opponent_search = MLB_ALIASES.get(opponent.lower(), opponent) if opponent else ""
    month_from = request.GET.get("month_from", "")
    month_to = request.GET.get("month_to", "")
    day_from = request.GET.get("day_from", "")
    day_to = request.GET.get("day_to", "")
    year_from = request.GET.get("year_from", "")
    year_to = request.GET.get("year_to", "")
    season_type = request.GET.get("season_type", "")
    sort = request.GET.get("sort", "newest")
    include_upcoming = request.GET.get("include_upcoming") == "1"
    games = Game.objects.filter(league="MLB")
    # By default, only show games that have already happened.
    # Checking "Include upcoming games" allows future games into the results.
    if not include_upcoming:
        games = games.filter(game_date__lte=date.today())

    if team:
        games = games.filter(
            Q(home_team__icontains=team_search) |
            Q(away_team__icontains=team_search)
        )

    if opponent:
        games = games.filter(
            Q(home_team__icontains=opponent_search) |
            Q(away_team__icontains=opponent_search)
        )

    if year_from and year_to:
        games = games.filter(
            game_date__year__gte=int(year_from),
            game_date__year__lte=int(year_to)
        )
    elif year_from:
        games = games.filter(game_date__year=int(year_from))
    elif year_to:
        games = games.filter(game_date__year=int(year_to))

    if month_from and month_to:
        games = games.filter(
            game_date__month__gte=int(month_from),
            game_date__month__lte=int(month_to)
        )
    elif month_from:
        games = games.filter(game_date__month=int(month_from))
    elif month_to:
        games = games.filter(game_date__month=int(month_to))

    if day_from and day_to:
        games = games.filter(
            game_date__day__gte=int(day_from),
            game_date__day__lte=int(day_to)
        )
    elif day_from:
        games = games.filter(game_date__day=int(day_from))
    elif day_to:
        games = games.filter(game_date__day=int(day_to))

    if season_type:
        games = games.filter(game_type=season_type)

    # Sorting
    if sort == "newest":
        games = games.order_by("-game_date")

    elif sort == "oldest":
        games = games.order_by("game_date")

    elif sort == "highest":
        games = games.annotate(
            avg_rating=Avg("gamelog__quality_rating")
        ).order_by("-avg_rating", "-game_date")

    elif sort == "lowest":
        games = games.annotate(
            avg_rating=Avg("gamelog__quality_rating")
        ).order_by("avg_rating", "-game_date")

    elif sort == "watched":
        games = games.annotate(
            watch_count=Count("gamelog")
        ).order_by("-watch_count", "-game_date")

    else:
        games = games.order_by("-game_date")

    if not any([
        team,
        opponent,
        year_from,
        year_to,
        month_from,
        month_to,
        day_from,
        day_to,
        season_type,
    ]):
        games = Game.objects.none()

    paginator = Paginator(games, 100)
    page_number = request.GET.get("page")
    games = paginator.get_page(page_number)

    return render(request, "mlb_games.html", {
        "games": games,
        "team": team,
        "opponent": opponent,
        "month_from": month_from,
        "month_to": month_to,
        "day_from": day_from,
        "day_to": day_to,
        "year_from": year_from,
        "year_to": year_to,
        "season_type": season_type,
        "sort": sort,
        "include_upcoming": include_upcoming,
    })


def nba_games(request):
    team = request.GET.get("team", "")
    opponent = request.GET.get("opponent", "")

    team_search = NBA_ALIASES.get(team.lower(), team) if team else ""
    opponent_search = NBA_ALIASES.get(opponent.lower(), opponent) if opponent else ""

    month_from = request.GET.get("month_from", "")
    month_to = request.GET.get("month_to", "")

    day_from = request.GET.get("day_from", "")
    day_to = request.GET.get("day_to", "")

    year_from = request.GET.get("year_from", "")
    year_to = request.GET.get("year_to", "")

    season_type = request.GET.get("season_type", "")
    sort = request.GET.get("sort", "newest")
    include_upcoming = request.GET.get("include_upcoming") == "1"

    games = Game.objects.filter(league="NBA")

    if not include_upcoming:
        games = games.filter(game_date__lte=date.today())

    if team:
        games = games.filter(
            Q(home_team__icontains=team_search) |
            Q(away_team__icontains=team_search)
        )

    if opponent:
        games = games.filter(
            Q(home_team__icontains=opponent_search) |
            Q(away_team__icontains=opponent_search)
        )

    if year_from and year_to:
        games = games.filter(
            game_date__year__gte=int(year_from),
            game_date__year__lte=int(year_to)
        )
    elif year_from:
        games = games.filter(game_date__year=int(year_from))
    elif year_to:
        games = games.filter(game_date__year=int(year_to))

    if month_from and month_to:
        games = games.filter(
            game_date__month__gte=int(month_from),
            game_date__month__lte=int(month_to)
        )
    elif month_from:
        games = games.filter(game_date__month=int(month_from))
    elif month_to:
        games = games.filter(game_date__month=int(month_to))

    if day_from and day_to:
        games = games.filter(
            game_date__day__gte=int(day_from),
            game_date__day__lte=int(day_to)
        )
    elif day_from:
        games = games.filter(game_date__day=int(day_from))
    elif day_to:
        games = games.filter(game_date__day=int(day_to))

    if season_type:
        games = games.filter(game_type=season_type)
    # Sorting
    if sort == "newest":
        games = games.order_by("-game_date")

    elif sort == "oldest":
        games = games.order_by("game_date")

    elif sort == "highest":
        games = games.annotate(
            avg_rating=Avg("gamelog__quality_rating")
        ).order_by("-avg_rating", "-game_date")

    elif sort == "lowest":
        games = games.annotate(
            avg_rating=Avg("gamelog__quality_rating")
        ).order_by("avg_rating", "-game_date")

    elif sort == "watched":
        games = games.annotate(
            watch_count=Count("gamelog")
        ).order_by("-watch_count", "-game_date")

    else:
        games = games.order_by("-game_date")
    if not any([
        team,
        opponent,
        month_from,
        month_to,
        day_from,
        day_to,
        year_from,
        year_to,
        season_type,
    ]):
        games = Game.objects.none()

    paginator = Paginator(games, 100)
    page_number = request.GET.get("page")
    games = paginator.get_page(page_number)

    return render(request, "nba_games.html", {
        "games": games,
        "team": team,
        "opponent": opponent,
        "month_from": month_from,
        "month_to": month_to,
        "day_from": day_from,
        "day_to": day_to,
        "year_from": year_from,
        "year_to": year_to,
        "season_type": season_type,
        "sort": sort,
        "include_upcoming": include_upcoming,
    })
def nfl_games(request):
    team = request.GET.get("team", "")
    opponent = request.GET.get("opponent", "")

    team_search = NFL_ALIASES.get(team.lower(), team) if team else ""
    opponent_search = NFL_ALIASES.get(opponent.lower(), opponent) if opponent else ""

    month_from = request.GET.get("month_from", "")
    month_to = request.GET.get("month_to", "")

    day_from = request.GET.get("day_from", "")
    day_to = request.GET.get("day_to", "")

    year_from = request.GET.get("year_from", "")
    year_to = request.GET.get("year_to", "")

    season_type = request.GET.get("season_type", "")
    sort = request.GET.get("sort", "newest")
    include_upcoming = request.GET.get("include_upcoming") == "1"

    games = Game.objects.filter(league="NFL")

    if not include_upcoming:
        games = games.filter(game_date__lte=date.today())

    if team:
        games = games.filter(
            Q(home_team__icontains=team_search) |
            Q(away_team__icontains=team_search)
        )

    if opponent:
        games = games.filter(
            Q(home_team__icontains=opponent_search) |
            Q(away_team__icontains=opponent_search)
        )

    # Year filtering
    if year_from and year_to:
        games = games.filter(
            game_date__year__gte=int(year_from),
            game_date__year__lte=int(year_to)
        )
    elif year_from:
        games = games.filter(game_date__year=int(year_from))
    elif year_to:
        games = games.filter(game_date__year=int(year_to))

    # Month filtering
    if month_from and month_to:
        games = games.filter(
            game_date__month__gte=int(month_from),
            game_date__month__lte=int(month_to)
        )
    elif month_from:
        games = games.filter(game_date__month=int(month_from))
    elif month_to:
        games = games.filter(game_date__month=int(month_to))

    # Day filtering
    if day_from and day_to:
        games = games.filter(
            game_date__day__gte=int(day_from),
            game_date__day__lte=int(day_to)
        )
    elif day_from:
        games = games.filter(game_date__day=int(day_from))
    elif day_to:
        games = games.filter(game_date__day=int(day_to))

    if season_type:
        games = games.filter(game_type=season_type)

    # Sorting
    if sort == "newest":
        games = games.order_by("-game_date")

    elif sort == "oldest":
        games = games.order_by("game_date")

    elif sort == "highest":
        games = games.annotate(
            avg_rating=Avg("gamelog__quality_rating")
        ).order_by("-avg_rating", "-game_date")

    elif sort == "lowest":
        games = games.annotate(
            avg_rating=Avg("gamelog__quality_rating")
        ).order_by("avg_rating", "-game_date")

    elif sort == "watched":
        games = games.annotate(
            watch_count=Count("gamelog")
        ).order_by("-watch_count", "-game_date")

    else:
        games = games.order_by("-game_date")

    if not any([
        team,
        opponent,
        month_from,
        month_to,
        day_from,
        day_to,
        year_from,
        year_to,
        season_type,
    ]):
        games = Game.objects.none()

    paginator = Paginator(games, 100)
    page_number = request.GET.get("page")
    games = paginator.get_page(page_number)

    return render(request, "nfl_games.html", {
        "games": games,
        "team": team,
        "opponent": opponent,
        "month_from": month_from,
        "month_to": month_to,
        "day_from": day_from,
        "day_to": day_to,
        "year_from": year_from,
        "year_to": year_to,
        "season_type": season_type,
        "sort": sort,
        "include_upcoming": include_upcoming,
    })

def champions_league(request):
    team = request.GET.get("team", "")
    opponent = request.GET.get("opponent", "")

    month_from = request.GET.get("month_from", "")
    month_to = request.GET.get("month_to", "")

    day_from = request.GET.get("day_from", "")
    day_to = request.GET.get("day_to", "")

    year_from = request.GET.get("year_from", "")
    year_to = request.GET.get("year_to", "")

    season_type = request.GET.get("season_type", "")
    sort = request.GET.get("sort", "newest")
    include_upcoming = request.GET.get("include_upcoming") == "1"

    games = Game.objects.filter(
        league="Soccer",
        competition="UEFA Champions League"
    )

    # By default, only show games that have already happened.
    # Checking "Include upcoming games" allows future games into the results.
    if not include_upcoming:
        games = games.filter(game_date__lte=timezone.localdate())

    if team:
        games = games.filter(
            Q(home_team__icontains=team) |
            Q(away_team__icontains=team)
        )

    if opponent:
        games = games.filter(
            Q(home_team__icontains=opponent) |
            Q(away_team__icontains=opponent)
        )

    if year_from:
        games = games.filter(game_date__year__gte=int(year_from))

    if year_to:
        games = games.filter(game_date__year__lte=int(year_to))

    if month_from:
        games = games.filter(game_date__month__gte=int(month_from))

    if month_to:
        games = games.filter(game_date__month__lte=int(month_to))

    if day_from:
        games = games.filter(game_date__day__gte=int(day_from))

    if day_to:
        games = games.filter(game_date__day__lte=int(day_to))

    if season_type:
        games = games.filter(game_type=season_type)

    # Sorting
    if sort == "newest":
        games = games.order_by("-game_date")

    elif sort == "oldest":
        games = games.order_by("game_date")

    elif sort == "highest":
        games = games.annotate(
            avg_rating=Avg("gamelog__quality_rating")
        ).order_by("-avg_rating", "-game_date")

    elif sort == "lowest":
        games = games.annotate(
            avg_rating=Avg("gamelog__quality_rating")
        ).order_by("avg_rating", "-game_date")

    elif sort == "watched":
        games = games.annotate(
            watch_count=Count("gamelog")
        ).order_by("-watch_count", "-game_date")

    else:
        games = games.order_by("-game_date")

    if not any([
        team,
        opponent,
        month_from,
        month_to,
        day_from,
        day_to,
        year_from,
        year_to,
        season_type,
    ]):
        games = Game.objects.none()

    paginator = Paginator(games, 100)
    page_number = request.GET.get("page")
    games = paginator.get_page(page_number)

    return render(request, "champions_league.html", {
        "games": games,
        "team": team,
        "opponent": opponent,
        "month_from": month_from,
        "month_to": month_to,
        "day_from": day_from,
        "day_to": day_to,
        "year_from": year_from,
        "year_to": year_to,
        "season_type": season_type,
        "sort": sort,
        "include_upcoming": include_upcoming,
    })

def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    average_quality = (
        GameLog.objects
        .filter(game=game, quality_rating__isnull=False)
        .aggregate(Avg("quality_rating"))
    )

    average_quality_rating = average_quality["quality_rating__avg"]

    if average_quality_rating is not None:
        average_quality_rating = round(average_quality_rating, 1)

    game_log = None

    rating_count = (
        GameLog.objects
        .filter(game=game, quality_rating__isnull=False)
        .count()
    )

    if request.user.is_authenticated:
        game_log = GameLog.objects.filter(
            user=request.user,
            game=game
        ).first()

    boxscore = None

    if game.league == "MLB":
        boxscore = get_linescore(game.game_id)

    comments = Comment.objects.filter(game=game)

    if request.method == "POST" and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)

        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.game = game
            comment.user = request.user
            comment.save()

            return redirect("game_detail", game_id=game.id)

    else:
        comment_form = CommentForm()

    return render(
        request,
        "game_detail.html",
        {
            "game": game,
            "game_log": game_log,
            "boxscore": boxscore,
            "average_quality_rating": average_quality_rating,
            "rating_count": rating_count,
            "comments": comments,
            "comment_form": comment_form,
        },
    )

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(
        Comment,
        id=comment_id,
        user=request.user,
    )

    game_id = comment.game.id

    if request.method == "POST":
        comment.delete()

    return redirect("game_detail", game_id=game_id)

@login_required
def log_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    game_log, created = GameLog.objects.get_or_create(
        user=request.user,
        game=game,
    )

    return redirect("edit_log", game_id=game.id)


@login_required
def edit_log(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    game_log = get_object_or_404(
        GameLog,
        user=request.user,
        game=game,
    )

    if request.method == "POST":
        form = GameLogForm(
            request.POST,
            instance=game_log,
            user=request.user,
        )

        if form.is_valid():
            log = form.save(commit=False)

            if log.watch_type == "HIGHLIGHTS":
                log.quality_rating = None
                log.experience_rating = None
                log.review = ""

            log.save()
            form.save_m2m()

            return redirect("game_detail", game_id=game.id)


    else:

        form = GameLogForm(

            instance=game_log,

            user=request.user,

        )

    return render(request, "edit_log.html", {
        "game": game,
        "form": form,
    })


@login_required
def diary(request):
    logs = (
        GameLog.objects.filter(user=request.user)
        .select_related("game")
        .order_by("-logged_at")
    )

    return render(request, "diary.html", {
        "logs": logs,
    })
@login_required
def stadiums(request, username=None):
    if username:
        profile_user = get_object_or_404(User, username=username)
    else:
        profile_user = request.user

    live_logs = (
        GameLog.objects.filter(
            user=profile_user,
            watch_type="LIVE",
        )
        .select_related("game")
    )

    stadium_counts = {}

    for log in live_logs:
        venue = log.game.venue or "Unknown Stadium"

        stadium_counts[venue] = stadium_counts.get(venue, 0) + 1

    stadiums = sorted(
        stadium_counts.items(),
        key=lambda x: (-x[1], x[0])
    )

    return render(request, "stadiums.html", {
        "stadiums": stadiums,
        "stadium_count": len(stadiums),
    })


@login_required
def logged_games(request, username=None, watch_type=None):
    if username:
        profile_user = get_object_or_404(User, username=username)
    else:
        profile_user = request.user

    logs = GameLog.objects.filter(user=profile_user)

    if watch_type:
        logs = logs.filter(watch_type=watch_type)

    logs = (
        logs.select_related("game")
        .order_by("-logged_at")
    )

    title = "All Logged Games"

    if watch_type == "LIVE":
        title = "Live Games"
    elif watch_type == "TV":
        title = "TV Games"
    elif watch_type == "REPLAY":
        title = "Replay Games"
    elif watch_type == "HIGHLIGHTS":
        title = "Highlight Games"

    return render(request, "diary.html", {
        "logs": logs,
        "title": title,
    })

def build_profile_context(profile_user):
    logs = (
        GameLog.objects.filter(user=profile_user)
        .select_related("game")
        .order_by("-logged_at")
    )

    live_stadium_count = (
        logs.filter(watch_type="LIVE")
        .values("game__venue")
        .exclude(game__venue="")
        .distinct()
        .count()
    )

    average_game_rating = (
        logs.filter(quality_rating__isnull=False)
        .aggregate(Avg("quality_rating"))["quality_rating__avg"]
    )

    average_experience_rating = (
        logs.filter(experience_rating__isnull=False)
        .aggregate(Avg("experience_rating"))["experience_rating__avg"]
    )

    if average_game_rating is not None:
        average_game_rating = round(average_game_rating, 1)

    if average_experience_rating is not None:
        average_experience_rating = round(
            average_experience_rating,
            1,
        )

    return {
        "profile_user": profile_user,
        "logs": logs,
        "total_logs": logs.count(),
        "live_count": logs.filter(watch_type="LIVE").count(),
        "tv_count": logs.filter(watch_type="TV").count(),
        "replay_count": logs.filter(watch_type="REPLAY").count(),
        "highlights_count": logs.filter(watch_type="HIGHLIGHTS").count(),
        "stadium_count": live_stadium_count,
        "favorite_count": logs.filter(favorite=True).count(),
        "average_game_rating": average_game_rating,
        "average_experience_rating": average_experience_rating,
    }

@login_required
def profile(request):
    context = build_profile_context(request.user)

    context["is_owner"] = True

    context["followers_count"] = Follow.objects.filter(
        following=request.user
    ).count()

    context["following_count"] = Follow.objects.filter(
        follower=request.user
    ).count()

    return render(request, "profile.html", context)

@login_required
def edit_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
        )

        if form.is_valid():
            form.save()
            return redirect("profile")

    else:
        form = ProfileForm(instance=profile)

    return render(request, "edit_profile.html", {
        "form": form,
    })

def public_profile(request, username):
    profile_user = get_object_or_404(User, username=username)

    context = build_profile_context(profile_user)

    context["is_owner"] = (
        request.user.is_authenticated
        and request.user == profile_user
    )

    is_following = False

    if request.user.is_authenticated and request.user != profile_user:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=profile_user,
        ).exists()

    followers_count = Follow.objects.filter(
        following=profile_user
    ).count()

    following_count = Follow.objects.filter(
        follower=profile_user
    ).count()

    context["is_following"] = is_following
    context["followers_count"] = followers_count
    context["following_count"] = following_count

    return render(request, "profile.html", context)

@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)

    if request.user == user_to_follow:
        return redirect("public_profile", username=username)

    follow = Follow.objects.filter(
        follower=request.user,
        following=user_to_follow,
    )

    if follow.exists():
        follow.delete()
    else:
        Follow.objects.create(
            follower=request.user,
            following=user_to_follow,
        )

    return redirect("public_profile", username=username)


def followers_list(request, username):
    profile_user = get_object_or_404(User, username=username)

    followers = (
        Follow.objects.filter(following=profile_user)
        .select_related("follower")
    )

    return render(request, "follow_list.html", {
        "profile_user": profile_user,
        "users": [follow.follower for follow in followers],
        "title": "Followers",
    })


def following_list(request, username):
    profile_user = get_object_or_404(User, username=username)

    following = (
        Follow.objects.filter(follower=profile_user)
        .select_related("following")
    )

    return render(request, "follow_list.html", {
        "profile_user": profile_user,
        "users": [follow.following for follow in following],
        "title": "Following",
    })

def user_search(request):


    query = request.GET.get("q", "")
    users = User.objects.none()

    if query:
        users = User.objects.filter(username__icontains=query)

    return render(request, "user_search.html", {
        "users": users,
        "query": query,
    })

def team_stats(logs, team_name):
    if not team_name:
        return {
            "games": 0,
            "game_rating": None,
            "experience_rating": None,
        }

    team_logs = logs.filter(
        Q(game__home_team=team_name) |
        Q(game__away_team=team_name)
    )

    return {
        "games": team_logs.count(),
        "game_rating": team_logs.filter(
            quality_rating__isnull=False
        ).aggregate(
            Avg("quality_rating")
        )["quality_rating__avg"],

        "experience_rating": team_logs.filter(
            experience_rating__isnull=False
        ).aggregate(
            Avg("experience_rating")
        )["experience_rating__avg"],
    }
@login_required
def stats(request):

    profile = request.user.profile

    logs = GameLog.objects.filter(user=request.user)

    overall_game = logs.filter(
        quality_rating__isnull=False
    ).aggregate(
        Avg("quality_rating")
    )["quality_rating__avg"]

    overall_experience = logs.filter(
        experience_rating__isnull=False
    ).aggregate(
        Avg("experience_rating")
    )["experience_rating__avg"]

    mlb_team = (
        MLB_ALIASES.get(
            profile.favorite_mlb_1.lower(),
            profile.favorite_mlb_1,
        )
        if profile.favorite_mlb_1
        else None
    )

    nba_team = (
        NBA_ALIASES.get(
            profile.favorite_nba_1.lower(),
            profile.favorite_nba_1,
        )
        if profile.favorite_nba_1
        else None
    )

    nfl_team = (
        NFL_ALIASES.get(
            profile.favorite_nfl_1.lower(),
            profile.favorite_nfl_1,
        )
        if profile.favorite_nfl_1
        else None
    )

    context = {
        "overall_game": overall_game,
        "overall_experience": overall_experience,

        "mlb": team_stats(logs, mlb_team),
        "nba": team_stats(logs, nba_team),
        "nfl": team_stats(logs, nfl_team),
        "nhl": team_stats(logs, profile.favorite_nhl_1),

        "mlb_team_name": profile.favorite_mlb_1,
        "nba_team_name": profile.favorite_nba_1,
        "nfl_team_name": profile.favorite_nfl_1,
        "nhl_team_name": profile.favorite_nhl_1,
    }

    return render(request, "stats.html", context)

def user_stats(request, username):
    user = get_object_or_404(User, username=username)

    profile = user.profile

    logs = GameLog.objects.filter(user=user)

    overall_game = logs.filter(
        quality_rating__isnull=False
    ).aggregate(
        Avg("quality_rating")
    )["quality_rating__avg"]

    overall_experience = logs.filter(
        experience_rating__isnull=False
    ).aggregate(
        Avg("experience_rating")
    )["experience_rating__avg"]

    mlb_team = (
        MLB_ALIASES.get(
            profile.favorite_mlb_1.lower(),
            profile.favorite_mlb_1,
        )
        if profile.favorite_mlb_1
        else None
    )

    nba_team = (
        NBA_ALIASES.get(
            profile.favorite_nba_1.lower(),
            profile.favorite_nba_1,
        )
        if profile.favorite_nba_1
        else None
    )

    nfl_team = (
        NFL_ALIASES.get(
            profile.favorite_nfl_1.lower(),
            profile.favorite_nfl_1,
        )
        if profile.favorite_nfl_1
        else None
    )

    context = {
        "overall_game": overall_game,
        "overall_experience": overall_experience,

        "mlb": team_stats(logs, mlb_team),
        "nba": team_stats(logs, nba_team),
        "nfl": team_stats(logs, nfl_team),
        "nhl": team_stats(logs, profile.favorite_nhl_1),

        "mlb_team_name": profile.favorite_mlb_1,
        "nba_team_name": profile.favorite_nba_1,
        "nfl_team_name": profile.favorite_nfl_1,
        "nhl_team_name": profile.favorite_nhl_1,
    }

    context["profile_user"] = user
    context["is_owner"] = False

    return render(request, "stats.html", context)