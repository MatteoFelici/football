from utils import get_key

DATA_PATH = './data'
COUNTRIES = ['IT', 'NL', 'GB', 'DE', 'FR', 'ES', 'PT']

ENDPOINTS = {
    'leagues': 'https://rapidapi.p.rapidapi.com/v2/leagues',
    'fixtures': 'https://rapidapi.p.rapidapi.com/v2/fixtures/league',
    'fixture_stats': 'https://api-football-v1.p.rapidapi.com/v2/statistics/'
                     'fixture',
    'player_stats': 'https://api-football-v1.p.rapidapi.com/v2/players/fixture'
}

HEADERS = {
    'x-rapidapi-host': "api-football-v1.p.rapidapi.com",
    'x-rapidapi-key': get_key()
}
