import os

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
BASE_URL = "https://api.football-data.org/v4"

# Leagues mapped to API codes
LEAGUES = {
    "PL": "Premier League",
    "ELC": "Championship",
    "PD": "La Liga",
    "BL1": "Bundesliga",
    "SA": "Serie A",
    "FL1": "Ligue 1"
}
