import os
import pandas as pd
import numpy as np

from params import DATA_PATH
from get_data import get_player_stats

NUM_FEATURES = ['rating', 'minutes_played']
CAT_FEATURES = ['player_name', 'team_name', 'position']
BOOL_FEATURES = ['captain', 'substitute']
STRUCT_FEATURES = ['shots', 'goals', 'passes', 'tackles', 'duels', 'dribbles',
                   'fouls', 'cards', 'penalty']


def json_to_pandas_player(j_player: dict) -> pd.DataFrame:
    """
    Return a pandas DataFrame row from a player statistics json. The structured
    features are unpacked.

    Parameters
    ----------
    j_player: dict
        Input json with player statistics

    Returns
    -------
    player_row: pandas DataFrame
        Row of a pandas DataFrame with player's data
    """

    # Build a new dictionary with processed data
    # Initiate with categorical features - they stay the same
    new_j = {x: j_player[x] for x in CAT_FEATURES}

    # Add numerical features forcing a float transformation
    new_j.update({x: np.float(j_player[x]) for x in NUM_FEATURES})

    # Add boolean features as real boolean
    new_j.update(
        {x: False if j_player[x] == 'False' else True for x in BOOL_FEATURES}
    )

    # For structured data, create a new key-value pair for each sub-key
    for feat in STRUCT_FEATURES:
        new_j.update({'.'.join([feat, x]): float(j_player[feat][x])
                      for x in j_player[feat]})

    # In order to return a DataFrame row, create an index with event/player IDs
    ind = '_'.join([str(j_player['event_id']), str(j_player['player_id'])])

    player_row = pd.DataFrame(new_j, index=[ind])

    return player_row


def process_fixture(fixture_id: int = None,
                    fixture_file: str = None,
                    stats_path: str = os.path.join(DATA_PATH,
                                                   'player_stats')
                    ) -> pd.DataFrame:
    """
    Given a fixture id or a path to a player statistics file, process statistics
    data to a pandas DataFrame.

    Parameters
    ----------
    fixture_id: int
        ID of the fixture for which to retrieve stats
    fixture_file: str
        Path to a player statistics json file
    stats_path: str, default os.path.join(params.DATA_PATH, 'player_stats')
        Path where to search for / download statistics data

    Returns
    -------
    players_stats: pandas.DataFrame
        Output DataFrame with processed data
    """

    if fixture_id is None and fixture_file is None:
        raise Exception('Both fixture ID and fixture file are None. You have '
                        'to provide one of these two informatiions.')
    j_fixture = get_player_stats(fixture_id, output_path=stats_path)

    players_stats = pd.DataFrame()
    for j_player in j_fixture['players']:
        players_stats = players_stats.append(json_to_pandas_player(j_player))

    return players_stats
