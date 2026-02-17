from rest_framework import serializers
from django.contrib.auth import get_user_model
from time import datetime
AppUser = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ['spotify_id', 'access_token', 'refresh_token', 'token_expiry', 'favourite_genres', 'favourite_artists', 'stats_retrieved_date', 'favourite_tracks']
        read_only_fields = ['spotify_id', 'access_token', 'refresh_token', 'token_expiry']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)

        cleaned = []
        for item in instance.favourite_tracks:
            # item is expected to be: [inner_list, datetime_string]
            if (
                isinstance(item, list)
                and len(item) == 2
            ):
                inner_list, dt_value = item
                # Convert datetime object → ISO string for JSON output
                if isinstance(dt_value, datetime):
                    dt_value = dt_value.isoformat()

                cleaned.append([inner_list, dt_value])
            else:
                cleaned.append(item)

        data["favourite_tracks"] = cleaned
        return data

    def to_internal_value(self, data):
        validated = super().to_internal_value(data)

        converted = []
        for item in validated.get("favourite_tracks", []):
            if (
                isinstance(item, list)
                and len(item) == 2
            ):
                inner_list, dt_value = item

                # Convert ISO string → datetime object
                if isinstance(dt_value, str):
                    try:
                        dt_value = datetime.fromisoformat(dt_value)
                    except ValueError:
                        pass

                converted.append([inner_list, dt_value])
            else:
                 converted.append(item)

        validated["favourite_tracks"] = converted
        return validated




    

