import os
import json
import requests
from utils import get_key
from params import DATA_PATH, COUNTRIES


LEAGUES_URL = "https://rapidapi.p.rapidapi.com/v2/leagues"
FIXTURES_URL = 'https://rapidapi.p.rapidapi.com/v2/fixtures/league'

HEADERS = {
    'x-rapidapi-host': "api-football-v1.p.rapidapi.com",
    'x-rapidapi-key': get_key()
}


def get_json_response(url: str, headers: dict = HEADERS) -> dict:
    """
    Basic call to api + response transposition to dict/json

    Parameters
    ----------
    url : str
        url of the API to request with GET
    headers : dict, default given
        Header for the request

    Returns
    -------
    r_dict : dict
        Json with the response form the API
    """

    response = requests.get(url, headers=headers)
    r_dict = json.loads(response.text)
    # If key "api" is in response, then we have results
    if 'api' in r_dict:
        return r_dict
    else:
        raise Exception(f"ERROR: {r_dict['message']}")


def get_leagues(output_path: str = DATA_PATH) -> dict:
    """
    Get all the leagues from the list of countries into params. Only leagues
    with players-statistics level of detail are allowed.
    If output file does not already exists at output_path, it will call the API
    and write the output.

    Parameters
    ----------
    output_path : str, default params.DATA_PATH
        The output path where to write leagues.json

    Returns
    -------
    leagues : dict
        Json with the list of leagues

    """

    output_file = os.path.join(output_path, 'leagues.json')

    # If file already exists, load into memory
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            leagues = json.load(f)

    # Otherwise, call the API
    else:
        r_dict = get_json_response(LEAGUES_URL)
        # Filter only leagues with player statistics level of detail
        leagues = {'leagues': [x for x in r_dict['api']['leagues'] if
                               x['coverage']['fixtures']['players_statistics']
                               and x['country_code'] in COUNTRIES]}

        # Write output
        with open(output_file, 'w') as f:
            json.dump(leagues, f, indent=4)

    return leagues


def get_fixtures(league_id, output_path=os.path.join(DATA_PATH, 'fixtures')):

    output_file = os.path.join(output_path, f'fixtures_{league_id}.json')

    # If file already exists, load into memory
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            fixtures = json.load(f)

    # Otherwise, call the API
    else:
        querystring = {"timezone": "Europe/London"}

        r_dict = get_json_response('/'.join([FIXTURES_URL, str(league_id)]))
        fixtures = {'fixtures': [x for x in r_dict['api']['fixtures']]}

        # Write output
        with open(output_file, 'w') as f:
            json.dump(fixtures, f, indent=4)

    return fixtures