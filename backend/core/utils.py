import requests
from datetime import datetime, timedelta, timezone
from django.conf import settings
from .models import AppUser 
import secrets
from django.shortcuts import redirect


class SpotifyAuth:
    AUTH_URL = "https://accounts.spotify.com/authorize"
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    PROFILE_URL = "https://api.spotify.com/v1/me"
    SCOPES = "user-read-private%20user-read-email%20playlist-read-private%20playlist-read-collaborative%20playlist-modify-public%20playlist-modify-private%20user-top-read"
    
    #generate the url to redirect user to spotify's auth page
    @classmethod
    def get_auth_url(cls,request):
        state=secrets.token_urlsafe(16)
        request.session['spotify_auth_state']=state
        
        return (
            f"{cls.AUTH_URL}?response_type=code"
            f"&client_id={settings.SPOTIFY_CLIENT_ID}"
            f"&redirect_uri={settings.SPOTIFY_REDIRECT_URI}"
            f"&scope={cls.SCOPES}"
            f"&state={state}"
            )
    #exchange the authorization code for access and refresh tokens, using csrf protection via state
    @classmethod
    def exchange_code_for_tokens(cls, code):
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "client_secret": settings.SPOTIFY_CLIENT_SECRET,
        }
        response = requests.post(cls.TOKEN_URL, data=payload)
        if response.status_code != 200:
            raise Exception("Failed to obtain tokens from Spotify")
        
        return response.json()
    #obtains the users spotify profile
    @classmethod
    def fetch_user_profile(cls, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(cls.PROFILE_URL, headers=headers)
        if response.status_code != 200:
            raise Exception("Failed to fetch Spotify profile")
        return response.json()
    #authenticate user using the authorization code, create or login user in the system
    @classmethod
    def authenticate_user(cls, code):
        tokens = cls.exchange_code_for_tokens(code)
        profile = cls.fetch_user_profile(tokens["access_token"])
        expiry = datetime.now(timezone.utc) + timedelta(seconds=tokens["expires_in"])
        user = AppUser.objects.create_or_login_user(
            spotify_id=profile["id"],
            favourite_genres=[],
            favourite_artists=[],
            favourite_tracks=[[],[],[]],
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_expiry=expiry,
            stats_retrieved_date=None
        )
        return user
    #refresh the access token using the refresh token
    @classmethod
    def refresh_access_token(cls, refresh_token):
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "client_secret": settings.SPOTIFY_CLIENT_SECRET,
        }
        response = requests.post(cls.TOKEN_URL, data=payload)
        if response.status_code != 200:
            raise Exception("Failed to refresh access token")
  
        return response.json()
    @classmethod
    def get_valid_access_token(cls, user):
        if user.token_expiry<=datetime.now(timezone.utc)-timedelta(minutes=5):
            tokens = cls.refresh_access_token(user.refresh_token)
            user.access_token = tokens["access_token"]
            user.token_expiry = datetime.now(timezone.utc) + timedelta(seconds=tokens["expires_in"])
            user.save()
        return user.access_token
    #gathers user's favourite genres from spotify
    @classmethod
    def fetch_user_favourite_artists(cls, user):
        access_token = cls.get_valid_access_token(user)
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{cls.PROFILE_URL}/top/artists", headers=headers, params={"limit":50, "time_range":"medium_term"})
        if response.status_code != 200:
            print(response.text)
            raise Exception("Failed to fetch user's top artists")
        return response.json()['items']
    #gather a user's favourite genres from their top artists
    @classmethod
    def fetch_user_favourite_genres(cls, user):
        tracks= cls.fetch_user_favourite_tracks(user) 
        if user.stats_retrieved_date and (datetime.now(timezone.utc) - user.stats_retrieved_date).days < 7:
            return user.favourite_genres, user.favourite_artists,tracks
        artists = cls.fetch_user_favourite_artists(user)
        genre_count = {}
        for artist in artists:
            for genre in artist.get('genres', []):
                genre_count[genre] = genre_count.get(genre, 0) + 1
        sorted_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)
        favourite_genres = [genre for genre, count in sorted_genres[:10]]
        user.favourite_genres = favourite_genres
        user.favourite_artists = [(artist['name'],artist['images'][0]['url']) for artist in artists[:10]]
        user.stats_retrieved_date = datetime.now()
        user.save()
        return favourite_genres,artists,tracks
    @classmethod
    def fetch_user_favourite_tracks(cls, user):
        #time_range: 0=short_term, 1=medium_term, 2=long_term
        #checks if data is needed to be fetched from spotify, if not returns cached data, otherwise fetches from spotify and updates the user model
        cls.check_user_stats(user)
        return user.favourite_tracks
        
       
    @classmethod
    def check_user_stats(cls, user):
        days=[7,30,112]
        time_range_str=["short_term","medium_term","long_term"]
        if len(user.favourite_tracks)==3:
            for i in range(3):
              if (user.favourite_tracks[i] ==[]) or ((datetime.now(timezone.utc) - datetime.fromisoformat(user.favourite_tracks[i][1])).days > days[i]):
                    #refreshes tracks list
                    access_token = cls.get_valid_access_token(user)
                    headers = {"Authorization": f"Bearer {access_token}"}
                    response = requests.get(f"{cls.PROFILE_URL}/top/tracks", headers=headers, params={"limit":50, "time_range":time_range_str[i]})
                    if response.status_code != 200:
                        raise Exception("Failed to fetch user's top tracks")
                    new_tracks = [[[track['name'], track['artists'][0]['name'], track['album']['images'][0]['url']] for track in response.json()['items']], datetime.now(timezone.utc).isoformat()]
                    user.favourite_tracks[i] = new_tracks
                    user.save()
      


                    
            
        
      

                    

            
        

            

      

        
    
    
class AppToken:
    @classmethod
    def refresh_token(cls,refresh):
         response=redirect("http://localhost:5173/")
         response.set_cookie("refresh", str(refresh), httponly=True,secure=True,samesite='None',max_age=60*60*24*30)
         response.set_cookie("access", str(refresh.access_token), httponly=True,secure=True,samesite='None',max_age=60*15)
         return response

class AppUserUtils:
    #returns user statistics
    @classmethod
    def get_user_stats(cls, user):
        favourite_genres, favourite_artists,favourite_tracks = SpotifyAuth.fetch_user_favourite_genres(user)
        favourite_tracks=[track[:-1] for track in favourite_tracks]
        return {
            "favourite_genres": favourite_genres,
            "favourite_artists": favourite_artists,
            "favourite_tracks": favourite_tracks,
        }
    





