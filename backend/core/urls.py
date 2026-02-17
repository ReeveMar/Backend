from django.urls import path

from core.views import SpotifyLoginView, SpotifyCallbackView,LogoutView,DisplayUserStatsView, RefreshTokenView

urlpatterns = [
    path("login/", SpotifyLoginView.as_view(), name="spotify-login"),
    path("callback/", SpotifyCallbackView.as_view(), name="spotify-callback"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", RefreshTokenView.as_view(), name="token-refresh"),
    path("users/me/", DisplayUserStatsView.as_view(), name="display-user-stats"),
  
]
