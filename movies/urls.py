from django.urls import path
from . import views


urlpatterns = [
    # List all movies or search/filter movies
    path('', views.get_movies, name='movie-list'),
    
    # Retrieve a specific movie by ID
    path('<int:pk>/', views.movie_detail, name='movie-detail'),
    
    # Trigger scraping
    path('trigger-scrape', views.trigger_scrape, name='trigger-scrape'),
]
