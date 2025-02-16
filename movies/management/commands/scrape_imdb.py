import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from movies.models import Movie
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import logging

PAGINATION_LIMIT = 0  # Set the number of times to click "Load More" button

# Set up logging
logger = logging.getLogger("scrape_imdb")


# Chrome options for headless mode
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Run in headless mode (no UI)
chrome_options.add_argument(
    "--disable-gpu"
)  # Disable GPU acceleration (helps in some environments)
chrome_options.add_argument(
    "--window-size=1920x1080"
)  # Set window size to avoid element detection issues
chrome_options.add_argument(
    "--no-sandbox"
)  # Bypass OS security model (useful for Linux servers)
chrome_options.add_argument(
    "--disable-dev-shm-usage"
)  # Overcomes limited resources in Docker containers


# Initialize WebDriver with the provided options
service = Service("/usr/local/bin/chromedriver")

# Constants

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

SEARCH_BASE_URL = "https://www.imdb.com/search/title/?title_type=feature"

IMDB_BASE_URL = "https://www.imdb.com"


class Command(BaseCommand):
    help = "Scrape IMDb movies by genre/keyword"

    def add_arguments(self, parser):
        parser.add_argument(
            "--genre", type=str, help="Genre or keyword to search", required=False
        )
        parser.add_argument(
            "--keyword", type=str, help="Genre or keyword to search", required=False
        )

    def fetch_content_by_genre(self, url):
        """
        Fetch content by genre or keyword using Selenium WebDriver
        """
        try:
            logger.debug(f"Fetching content from URL: {url}")

            driver = webdriver.Chrome(
                service=service, options=chrome_options
            )  # Use webdriver for your specific browser
            driver.get(url)  # Replace with the target URL

            # Define a wait object
            wait = WebDriverWait(driver, 10)

            # Function to load more results
            def click_load_more():
                try:
                    # Wait for the "Load More" button to be clickable
                    load_more_button = wait.until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "button.ipc-see-more__button")
                        )
                    )

                    # Scroll the button into view
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});",
                        load_more_button,
                    )

                    time.sleep(2)  # Wait for the button to stabilize

                    # Click the button using JavaScript to avoid interception issues
                    driver.execute_script("arguments[0].click();", load_more_button)

                    return True
                except Exception as e:
                    logger.error(f"Load More button not found or not clickable: {e}")
                    return False  # Stop when the button is no longer found or clickable

            pagination_count = 0  # Initialize the pagination counter

            # Click "Load More" button multiple times until it's unavailable
            while click_load_more() and pagination_count < PAGINATION_LIMIT:
                logger.debug(
                    f"Clicked 'Load More' button {pagination_count + 1} time(s)"
                )
                pagination_count += 1

            # Extract the updated page content after all items are loaded
            page_source = driver.page_source

            # Close WebDriver
            driver.quit()

            # Process the page_source using BeautifulSoup or any parser
            soup = BeautifulSoup(page_source, "html.parser")

            return soup
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return None

    def fetch_director_and_cast_detail(self, url):
        """
        Fetch director and cast details from the movie page
        """
        try:
            logger.debug(f"Fetching director and cast details from URL: {url}")

            response = requests.get(url, headers=HEADERS)
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract director name
            director = (
                soup.select_one("a.ipc-metadata-list-item__list-content-item").get_text(
                    strip=True
                )
                if soup.select_one("a.ipc-metadata-list-item__list-content-item")
                else "N/A"
            )

            # Extract cast
            cast_section = soup.find_all(
                "div", attrs={"data-testid": "shoveler-items-container"}
            )
            cast_name_list = []

            for cast in cast_section:
                cast_names = cast.find_all(
                    "a", attrs={"data-testid": "title-cast-item__actor"}
                )
                for cast_name in cast_names:
                    cast_name_list.append(cast_name.get_text(strip=True))

            all_cast_names = ", ".join(cast_name_list) if cast_name_list else "N/A"

            return director, all_cast_names
        except Exception as e:
            logger.error(
                f"Error fetching director and cast details from URL: {url}, Exception: {e}"
            )
            return None, None

    def get_plot_summary(self, url):
        try:
            response = requests.get(url, headers=HEADERS)
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract plot summary
            plot_summary = (
                soup.select_one("li.ipc-metadata-list__item").get_text(strip=True)
                if soup.select_one("li.ipc-metadata-list__item")
                else "N/A"
            )

            return plot_summary
        except Exception as e:
            logger.error(f"Error fetching plot summary from URL: {url}, Exception: {e}")
            return None

    def process_movie(self, movie, IMDB_BASE_URL):
        """
        Extract movie details and save them into the database
        """
        try:
            # Extract title
            title = movie.select_one("h3.ipc-title__text").get_text(strip=True)

            # Clean title (remove ranking number)
            if ". " in title:
                title = title.split(". ", 1)[1]

            # Extract year
            year = (
                movie.select_one("span.dli-title-metadata-item").get_text(strip=True)
                if movie.select_one("span.dli-title-metadata-item")
                else None
            )

            # Extract rating
            rating = (
                movie.select_one("span.ipc-rating-star--imdb")
                .get_text(strip=True)
                .split()[0]
                if movie.select_one("span.ipc-rating-star--imdb")
                else None
            )

            # Extract url
            if movie.select_one("a.ipc-title-link-wrapper"):
                url = (
                    IMDB_BASE_URL + movie.select_one("a.ipc-title-link-wrapper")["href"]
                )
            else:
                url = None

            # Fetch director and cast details
            director, cast, plot_summary = None, None, None
            if url:
                # Extract page ID from URL using string manipulation
                page_id = url.split("/title/")[1].split("/")[0]
                plot_summary_url = f"{IMDB_BASE_URL}/title/{page_id}/plotsummary"

                director, cast = self.fetch_director_and_cast_detail(url)

                # Fetch plot summary
                plot_summary = self.get_plot_summary(plot_summary_url)

            # Save data into database using model
            movie_obj = Movie.objects.create(
                title=title,
                release_year=int(year),
                imdb_rating=rating,
                directors=director,
                cast=cast,
                plot_summary=plot_summary,
                imdb_url=url,
                genre=self.genre,
            )
            movie_obj.save()
        except Exception as e:
            logger.error(
                f"Error processing movie: {title}, Year: {year}, Rating: {rating}, URL: {url}, Exception: {e}"
            )

    def handle(self, *args, **options):
        """
        Main method to handle scraping
        """

        logger.info("Scraping initiated")

        # Get genre from command line
        self.genre = options["genre"]
        self.keyword = options["keyword"]

        # Create URL based on genre or keyword
        search_url = SEARCH_BASE_URL
        if self.genre:
            search_url += f"&genres={self.genre}"
        if self.keyword:
            search_url += f"&keywords={self.keyword}"

        # Fetch content
        soup = self.fetch_content_by_genre(search_url)

        # Find all movie containers
        movie_containers = soup.select("li.ipc-metadata-list-summary-item")

        # Extract movie data sequentially with a delay
        for movie in movie_containers:
            self.process_movie(movie, IMDB_BASE_URL)
            time.sleep(1)  # Delay of 1 second between requests

        logger.info("Scraping completed")
