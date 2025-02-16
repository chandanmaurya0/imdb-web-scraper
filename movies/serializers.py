from rest_framework import serializers
from movies.models import Movie

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = '__all__'




class ScrapeRequestSerializer(serializers.Serializer):
    genre = serializers.CharField(required=False, max_length=100)
    keyword = serializers.CharField(required=False, max_length=100)

    def validate(self, data):
        if not data.get('genre') and not data.get('keyword'):
            raise serializers.ValidationError("At least one of 'genre' or 'keyword' must be provided.")
        return data