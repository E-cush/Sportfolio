from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from .team_logos import TEAM_LOGOS
from .team_choices import (
    MLB_TEAMS,
    NBA_TEAMS,
    NFL_TEAMS,
    NHL_TEAMS,
)


class Game(models.Model):
    game_id = models.BigIntegerField(unique=True)
    status = models.CharField(max_length=40)
    league = models.CharField(max_length=20)
    competition = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    event_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
    )

    racing_series = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    season = models.IntegerField()
    game_type = models.CharField(max_length=30, null=True, blank=True)
    home_team = models.CharField(max_length=100)
    away_team = models.CharField(max_length=100)

    game_date = models.DateField()

    game_start = models.DateTimeField(
        null=True,
        blank=True,
    )

    game_finished_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    home_score = models.IntegerField()
    away_score = models.IntegerField()

    venue = models.CharField(max_length=100)

    @property
    def is_upcoming(self):
        return self.game_date > timezone.now().date()

    @property
    def home_logo(self):
        return TEAM_LOGOS.get((self.league, self.home_team), "")

    @property
    def away_logo(self):
        return TEAM_LOGOS.get((self.league, self.away_team), "")

    @property
    def live_chat_available(self):
        if not self.game_start:
            return False

        now = timezone.now()

        chat_opens = self.game_start - timedelta(minutes=30)

        # Too early for the chat
        if now < chat_opens:
            return False

        closed_statuses = {
            "cancelled",
            "canceled",
            "postponed",
            "abandoned",
        }

        if self.status.lower() in closed_statuses:
            return False

        final_statuses = {
            "final",
            "completed",
            "finished",
        }

        # If the game is already finished but we don't have
        # a recorded finish time, keep the chat closed.
        if self.status.lower() in final_statuses:
            if not self.game_finished_at:
                return False

            chat_closes = self.game_finished_at + timedelta(minutes=30)

            return now <= chat_closes

        # Game is currently in progress
        return True

    def save(self, *args, **kwargs):
        if self.pk:
            existing = (
                type(self)
                .objects
                .filter(pk=self.pk)
                .values("status", "game_finished_at")
                .first()
            )

            if existing:
                old_status = (existing["status"] or "").lower()
                new_status = (self.status or "").lower()

                final_statuses = {
                    "final",
                    "completed",
                    "finished",
                }

                if (
                        new_status in final_statuses
                        and old_status not in final_statuses
                        and existing["game_finished_at"] is None
                ):
                    self.game_finished_at = timezone.now()

                    update_fields = kwargs.get("update_fields")

                    if update_fields is not None:
                        kwargs["update_fields"] = set(update_fields) | {
                            "game_finished_at"
                        }

        super().save(*args, **kwargs)

    def __str__(self):
        if self.league == "Racing" and self.event_name:
            return f"{self.event_name} ({self.game_date})"

        return f"{self.away_team} @ {self.home_team} ({self.game_date})"


class GameLog(models.Model):
    WATCH_CHOICES = [
        ("LIVE", "Attended Live"),
        ("TV", "Watched Live on TV"),
        ("REPLAY", "Watched Replay"),
        ("HIGHLIGHTS", "Highlights Only"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)

    watched_with = models.ManyToManyField(
        User,
        blank=True,
        related_name="games_watched_with",
    )

    logged_at = models.DateTimeField(auto_now_add=True)

    quality_rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        null=True,
        blank=True,
    )

    experience_rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        null=True,
        blank=True,
    )

    watch_type = models.CharField(
        max_length=10,
        choices=WATCH_CHOICES,
        null=True,
        blank=True,
    )

    favorite = models.BooleanField(
        default=False
    )

    review = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} logged {self.game}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "game"],
                name="unique_user_game_log",
            )
        ]

class ReviewLike(models.Model):
    review = models.ForeignKey(
        GameLog,
        on_delete=models.CASCADE,
        related_name="likes",
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="review_likes",
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["review", "user"],
                name="unique_review_like",
            )
        ]

    def __str__(self):
        return f"{self.user.username} liked review {self.review.id}"

class GameChatMessage(models.Model):
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="chat_messages",
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    message = models.TextField(
        max_length=500,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.username}: {self.message[:40]}"

class Comment(models.Model):
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    text = models.TextField(max_length=1000)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username}: {self.game}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    bio = models.TextField(
        max_length=500,
        blank=True,
    )

    favorite_mlb_1 = models.CharField(
        max_length=3,
        choices=MLB_TEAMS,
        blank=True,
    )

    favorite_mlb_2 = models.CharField(
        max_length=3,
        choices=MLB_TEAMS,
        blank=True,
    )

    favorite_nba_1 = models.CharField(
        max_length=3,
        choices=NBA_TEAMS,
        blank=True,
    )

    favorite_nba_2 = models.CharField(
        max_length=3,
        choices=NBA_TEAMS,
        blank=True,
    )

    favorite_nfl_1 = models.CharField(
        max_length=3,
        choices=NFL_TEAMS,
        blank=True,
    )

    favorite_nfl_2 = models.CharField(
        max_length=3,
        choices=NFL_TEAMS,
        blank=True,
    )

    favorite_nhl_1 = models.CharField(
        max_length=3,
        choices=NHL_TEAMS,
        blank=True,
    )

    favorite_nhl_2 = models.CharField(
        max_length=3,
        choices=NHL_TEAMS,
        blank=True,
    )

    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Follow(models.Model):
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
    )

    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="followers",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"],
                name="unique_follow",
            )
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

