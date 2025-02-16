# IMDB Web Scraper

## Project Description
This project is a web scraper for IMDb that extracts movie details based on genre or keyword. It uses Django for the backend and Selenium for web scraping.

## Setup Instructions

1. Clone the repository:
    ```sh
    git clone https://github.com/chandanmaurya0/imdb-web-scraper.git
    cd imdb-web-scraper
    ```

2. Create a virtual environment and activate it:
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Download and set up ChromeDriver (for Selenium):
    - Download ChromeDriver from [here](https://googlechromelabs.github.io/chrome-for-testing/#stable).
    - Extract the downloaded file.
    - Move the `chromedriver` executable to a directory that’s in your system’s PATH. A common location is `/usr/local/bin/`.
    - You can do this by running the following commands in Terminal:
        ```sh
        unzip chromedriver_mac64.zip
        sudo mv chromedriver /usr/local/bin/
        ```

5. Run database migrations:
    ```sh
    python manage.py migrate
    ```

6. Start the Django development server:
    ```sh
    python manage.py runserver
    ```

## Usage

### List all movies or search/filter movies
- Endpoint: `/movies/`
- Method: `GET`
- Query Parameters: `genre` (optional)

### Retrieve a specific movie by ID
- Endpoint: `/movies/<int:pk>/`
- Method: `GET`

### Trigger scraping via API
- Endpoint: `/movies/trigger-scrape`
- Method: `POST`
- Expected POST data: `{"genre": "comedy"}`

### Trigger scraping via command
You can also trigger web scraping using a management command:
```sh
python manage.py scrape_imdb --genre comedy --keyword fight
```

## Logging
Logs are stored in the `logs/imdb_api.log` file.