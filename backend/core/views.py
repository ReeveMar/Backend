from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .utils import SpotifyAuth, AppToken, AppUserUtils
from django.shortcuts import redirect

#login view
class SpotifyLoginView(APIView):
    permission_classes = []
    authentication_classes = []
    def get(self, request):
        auth_url= SpotifyAuth.get_auth_url(request)
        return redirect(auth_url)


#handles callback
class SpotifyCallbackView(APIView):
    permission_classes = []
    authentication_classes = []
    def get(self, request):
        #handles csrf protection via state parameter
        code = request.query_params.get("code")
        state= request.query_params.get("state")
        if state != request.session.get('spotify_auth_state'):
            return Response({"error": "State mismatch. Possible CSRF attack."}, status=400)
        if not code:
            return Response({"error": "Missing authorization code"}, status=400)
        try:
            user = SpotifyAuth.authenticate_user(code)
            refresh = RefreshToken.for_user(user)
            return AppToken.refresh_token(refresh)

        except Exception as e:
            return Response({"error": str(e)}, status=400)
#handles token refreshing
class RefreshTokenView(APIView):
    def post(self, request):
        refresh_token= request.COOKIES.get("refresh")
        if not refresh_token:
            return Response({"error": "No refresh token provided"}, status=400)
        try:
            token=RefreshToken(refresh_token)
            return AppToken.refresh_token(token)


        except Exception:
            return Response({"error": "Invalid refresh token"}, status=400)
#directs to stats page
class DisplayUserStatsView(APIView):  
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user= request.user
        stats= AppUserUtils.get_user_stats(user)
        return Response(stats)

#directs to logout
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            token = RefreshToken(request.COOKIES.get("refresh"))
            token.blacklist()
            return Response({"success": "Logged out successfully"})
        except Exception:
            return Response({"error": "Invalid token"}, status=400)