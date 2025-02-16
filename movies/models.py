from django.db import models

# Create your models here.
class Movie(models.Model):
    title = models.CharField(max_length=255)
    release_year = models.IntegerField()
    imdb_rating = models.CharField(max_length=100, null=True)
    directors = models.CharField(max_length=255)
    cast = models.TextField()
    plot_summary = models.TextField(null=True)
    genre = models.CharField(max_length=100, null=True)
    imdb_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
