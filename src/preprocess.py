import os
import json
import pandas as pd

from utils import safe_num_cast


class LeagueData:
    """
    This class encapsulate all the methods to process and analyse league-level
    data
    """

    def __init__(self):
        pass


class PlayerData:
    """
    This class encapsulate all the methods to process and analyse player-level
    staistics
    """

    def __init__(self,
                 num_features=None,
                 cat_features=None,
                 bool_features=None,
                 struct_features=None):
        """
        Parameters
        ----------
        num_features: list
            List of features to retrieve from json.
            Default is ['rating', 'minutes_played']
        cat_features: list
            List of features to retrieve from json.
            Default is ['player_name', 'team_name', 'position']
        bool_features: list
            List of features to retrieve from json.
            Default is ['captain', 'substitute']
        struct_features: list
            List of features to retrieve from json.
            Default is ['shots', 'goals', 'passes', 'tackles', 'duels', 'dribbles',
            'fouls', 'cards', 'penalty']
        """

        if num_features is None:
            num_features = ['rating', 'minutes_played']
        if cat_features is None:
            cat_features = ['player_name', 'team_name', 'position']
        if bool_features is None:
            bool_features = ['captain', 'substitute']
        if struct_features is None:
            struct_features = ['shots', 'goals', 'passes', 'tackles',
                               'duels', 'dribbles', 'fouls', 'cards',
                               'penalty']
        self.num_features = num_features
        self.cat_features = cat_features
        self.bool_features = bool_features
        self.struct_features = struct_features

    def json_to_pandas_player(self,
                              j_player: dict) -> pd.DataFrame:
        """
        Return a pandas DataFrame row from a player statistics json. The
        structured features are unpacked.

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
        new_j = {x: j_player[x] for x in self.cat_features}

        # Add numerical features forcing a float transformation
        new_j.update({x: safe_num_cast(j_player[x]) for x in self.num_features})

        # Add boolean features as real boolean
        new_j.update(
            {x: True if j_player[x] == 'True' else False
             for x in self.bool_features}
        )

        # For structured data, create a new key-value pair for each sub-key
        for feat in self.struct_features:
            new_j.update({'.'.join([feat, x]): safe_num_cast(j_player[feat][x])
                          for x in j_player[feat]})

        # In order to return a DataFrame row, create an index with
        # event/player IDs
        ind = '_'.join([str(j_player['event_id']), str(j_player['player_id'])])

        player_row = pd.DataFrame(new_j, index=[ind])

        return player_row

    def process_fixture(self,
                        fixture_file: str) -> pd.DataFrame:
        """
        Given a path to a player statistics file, process statistics data to a
        pandas DataFrame.

        Parameters
        ----------
        fixture_file: str
            Path to a player statistics json file

        Returns
        -------
        players_stats: pandas.DataFrame
            Output DataFrame with processed data
        """

        # Load data into dict
        with open(fixture_file, 'r') as f:
            j_fixture = json.load(f)

        # Initialize empty dataframe
        players_stats = pd.DataFrame()

        # Iterate on each player and append to DataFrame
        for j_player in j_fixture['players']:
            players_stats = players_stats.append(
                self.json_to_pandas_player(j_player)
            )

        return players_stats

    def process_league(self,
                       league_path: str) -> pd.DataFrame:
        """
        Given a path to a directory with player statistics files, process
        each file and store all data into a pandas DataFrame.

        Parameters
        ----------
        league_path: str
            Path to directory with player statistics files

        Returns
        -------
        league_data: pandas.DataFrame
            Output DataFrame with processed data

        """

        files = os.listdir(league_path)
        tot_files = len(files)

        # Initialize empty dataframe
        league_data = pd.DataFrame()

        # Iterate on each fixture and append to DataFrame
        for i, fixture_file in enumerate(files):
            print(f'{i + 1} / {tot_files} --- {fixture_file}')
            league_data = league_data.append(
                self.process_fixture(
                    fixture_file=os.path.join(league_path, fixture_file)
                )
            )

        return league_data
