from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from movies.models import Movie
from unittest.mock import patch
from movies.management.commands.scrape_imdb import Command, HEADERS

class MovieModelTests(TestCase):
    def test_create_movie(self):
        """Test creating a movie object with all required fields"""
        movie = Movie.objects.create(
            title="Test Movie",
            release_year=2023,
            imdb_rating="7.5(5k)",
            directors="Test Director",
            cast="Actor1, Actor2",
            plot_summary="Test plot summary",
            genre="action",
            imdb_url="http://example.com"
        )
        
        self.assertEqual(movie.title, "Test Movie")
        self.assertEqual(movie.release_year, 2023)
        self.assertEqual(str(movie), "Test Movie")  # Test __str__ method

class MovieViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.movie = Movie.objects.create(
            title="Test Movie",
            release_year=2023,
            imdb_rating="7.5(5k)",
            directors="Test Director",
            cast="Actor1, Actor2",
            plot_summary="Test plot summary",
            genre="action",
            imdb_url="http://example.com"
        )

    def test_get_all_movies(self):
        """Test retrieving list of movies"""
        response = self.client.get(reverse('movie-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['title'], "Test Movie")

    def test_get_single_movie(self):
        """Test retrieving a single movie by ID"""
        url = reverse('movie-detail', args=[self.movie.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], "Test Movie")

    def test_filter_movies_by_genre(self):
        """Test filtering movies by genre"""
        response = self.client.get(reverse('movie-list'), {'genre': 'action'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)


class ScrapeViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.invalid_payload = {"invalid_key": "invalid_value"}

    def test_trigger_scrape_invalid(self):
        """Test triggering scrape with invalid data"""
        response = self.client.post(
            reverse('trigger-scrape'),
            self.invalid_payload,
            format='json'
        )
        self.assertEqual(response.status_code, 400)



class ScrapeIMDBTests(TestCase):

    @patch('movies.management.commands.scrape_imdb.webdriver.Chrome')
    def test_fetch_content_by_genre(self, MockWebDriver):
        """Test fetching content by genre using Selenium WebDriver"""
        mock_driver = MockWebDriver.return_value
        mock_driver.page_source = "<html><div class='lister-item-content'></div></html>"
        
        command = Command()
        url = "http://example.com"
        soup = command.fetch_content_by_genre(url)
        
        self.assertIsNotNone(soup)
        self.assertIn('lister-item-content', str(soup))
        mock_driver.get.assert_called_once_with(url)
        mock_driver.quit.assert_called_once()

    @patch('movies.management.commands.scrape_imdb.requests.get')
    def test_fetch_director_and_cast_detail(self, mock_get):
        """Test fetching director and cast details from the movie page"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = """
            <html>
                <a class="ipc-metadata-list-item__list-content-item">Test Director</a>
                <div data-testid="shoveler-items-container">
                    <a data-testid="title-cast-item__actor">Actor1</a>
                    <a data-testid="title-cast-item__actor">Actor2</a>
                </div>
            </html>
        """
        
        command = Command()
        url = "http://example.com"
        director, cast = command.fetch_director_and_cast_detail(url)
        
        self.assertEqual(director, "Test Director")
        self.assertEqual(cast, "Actor1, Actor2")
        mock_get.assert_called_once_with(url, headers=HEADERS)

    @patch('movies.management.commands.scrape_imdb.requests.get')
    def test_get_plot_summary(self, mock_get):
        """Test fetching plot summary from the movie page"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = """
            <html>
                <li class="ipc-metadata-list__item">Test plot summary</li>
            </html>
        """
        
        command = Command()
        url = "http://example.com"
        plot_summary = command.get_plot_summary(url)
        
        self.assertEqual(plot_summary, "Test plot summary")
        mock_get.assert_called_once_with(url, headers=HEADERS)

