from django import forms
from django.contrib.auth.models import User
from .models import GameLog, Profile, Comment, Follow

class GameLogForm(forms.ModelForm):
    class Meta:
        model = GameLog
        fields = [
            "watch_type",
            "quality_rating",
            "experience_rating",
            "favorite",
            "review",
            "watched_with",
        ]

        widgets = {
            "quality_rating": forms.Select(choices=[
                ("", "---------"),
                (1, "★☆☆☆☆"),
                (2, "★★☆☆☆"),
                (3, "★★★☆☆"),
                (4, "★★★★☆"),
                (5, "★★★★★"),
            ]),
            "experience_rating": forms.Select(choices=[
                ("", "---------"),
                (1, "★☆☆☆☆"),
                (2, "★★☆☆☆"),
                (3, "★★★☆☆"),
                (4, "★★★★☆"),
                (5, "★★★★★"),
            ]),
            "review": forms.Textarea(attrs={
                "rows": 6,
                "placeholder": "What did you think of the game?",
            }),
            "watched_with": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        self.fields["watch_type"].required = True
        self.fields["quality_rating"].required = False
        self.fields["experience_rating"].required = False
        self.fields["review"].required = False
        self.fields["watched_with"].required = False

        if user:
            self.fields["watched_with"].queryset = User.objects.filter(
                followers__follower=user
            ).distinct()

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "bio",
            "favorite_mlb_1",
            "favorite_nba_1",
            "favorite_nfl_1",
            "favorite_nhl_1",
            "profile_picture",
        ]

        widgets = {
            "bio": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Tell everyone about yourself...",
            }),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]

        widgets = {
            "text": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Join the discussion..."
            })
        }