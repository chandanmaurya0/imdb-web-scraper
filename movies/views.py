from movies.models import Movie
from movies.serializers import MovieSerializer, ScrapeRequestSerializer
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework import status
from django.core.management import call_command
import logging

# Get an instance of a logger
logger = logging.getLogger("movies_views")


@api_view(["GET"])
def get_movies(request):
    """
    List all the movies with optional filters
    """

    # Get genre from the query params
    genre = request.query_params.get("genre", None)
    if genre:
        movies = Movie.objects.filter(genre=genre)
    else:
        movies = Movie.objects.all()

    serializer = MovieSerializer(movies, many=True)
    return JsonResponse(serializer.data, safe=False)


@api_view(["GET"])
def movie_detail(request, pk):
    """
    Retrieve a specific movie by ID.
    """
    try:
        movie = Movie.objects.get(pk=pk)
        serializer = MovieSerializer(movie)
        return Response(serializer.data)
    except Movie.DoesNotExist:
        logger.error(f"Movie with ID {pk} not found")
        return Response({"error": "Movie not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
def trigger_scrape(request):
    """
    Trigger scraping of movies based on genre or keyword.
    Expected POST data: {"genre": "comedy"}
    """
    serializer = ScrapeRequestSerializer(data=request.data)
    if not serializer.is_valid():
        logger.error("Invalid scrape request data")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Call management command with parameters
        call_command("scrape_imdb", genre=serializer.validated_data.get("genre"), keyword=serializer.validated_data.get("keyword"))
        return Response(
            {"status": "Scraping initiated successfully"},
            status=status.HTTP_202_ACCEPTED,
        )
    except Exception as e:
        logger.exception("Error triggering scraping")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
