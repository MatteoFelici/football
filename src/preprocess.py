import os
import json
import datetime
import pandas as pd

from utils import safe_num_cast


class LeagueData:
    """
    This class encapsulate all the methods to process and analyse league-level
    data
    """

    def __init__(self,
                 id_features=None,
                 num_features=None,
                 cat_features=None,
                 bool_features=None,
                 struct_features=None):
        """
        Parameters
        ----------
        id_features: list
            List od IDs to retrieve from json.
            Default is ['league_id', 'fixture_id']
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

        if id_features is None:
            id_features = ['league_id', 'fixture_id']
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
        self.id_features = id_features
        self.num_features = num_features
        self.cat_features = cat_features
        self.bool_features = bool_features
        self.struct_features = struct_features

    def json_to_pandas_league(self,
                              j_fixture: dict) -> pd.DataFrame:
        """
        Return a pandas DataFrame row from a fixture info json.

        Parameters
        ----------
        j_fixture: dict
            Input json with fixture info

        Returns
        -------
        fixture_data: pandas.DataFrame
            Row of a pandas DataFrame with processed fixture info
        """

        # Numerical data
        new_j = {x: j_fixture[x] for x in ['elapsed', 'goalsHomeTeam',
                                           'goalsAwayTeam']}
        # League info
        new_j.update(
            {'league_' + x: j_fixture['league'][x] for x in ['name', 'country']}
        )
        # Epoch to datetime
        new_j['fixture_date'] = datetime.datetime.fromtimestamp(
            j_fixture['event_timestamp']
        )

        # Structured data
        new_j.update({'.'.join([x, y.replace('team_', '')]): j_fixture[x][y]
                      for x in ['homeTeam', 'awayTeam']
                      for y in ['team_id', 'team_name']})
        new_j.update({'.'.join(['score', x]): j_fixture['score'][x]
                      for x in j_fixture['score']})

        # In order to return a DataFrame row, create an index with
        # concatenation of IDs
        ind = '_'.join([str(j_fixture[feat])
                        for feat in ['league_id', 'fixture_id']])

        fixture_row = pd.DataFrame(new_j, index=[ind])

        return fixture_row

    def json_to_pandas_fixture_stats(self,
                                     j_fixture: dict,
                                     fixture_id: int) -> pd.DataFrame:
        """
        Return a pandas DataFrame row from a fixture statistics json. The
        structured features are unpacked.

        Parameters
        ----------
        j_fixture: dict
            Input json with fixture statistics
        fixture_id: int
            ID of the fixture to use as index for DataFrame

        Returns
        -------
        player_row: pandas DataFrame
            Row of a pandas DataFrame with fixture stats data
        """

        # Build a new dictionary with processed data
        # First add home data
        new_j = {'.'.join(['home', feat.replace(' ', '_')]):
                 safe_num_cast(j_fixture[feat]['home'])
                 for feat in j_fixture}
        # Then add away data
        new_j.update({'.'.join(['away', feat.replace(' ', '_')]):
                      safe_num_cast(j_fixture[feat]['away'])
                      for feat in j_fixture})

        player_row = pd.DataFrame(new_j, index=[fixture_id])

        return player_row


class PlayerData:
    """
    This class encapsulate all the methods to process and analyse player-level
    staistics
    """

    def __init__(self,
                 id_features=None,
                 num_features=None,
                 cat_features=None,
                 bool_features=None,
                 struct_features=None):
        """
        Parameters
        ----------
        id_features: list
            List od IDs to retrieve from json.
            Default is ['event_id', 'player_id', 'team_id']
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

        if id_features is None:
            id_features = ['event_id', 'player_id', 'team_id']
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
        self.id_features = id_features
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
        player_row: pandas.DataFrame
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
        # concatenation of id_features
        ind = '_'.join([str(j_player[feat]) for feat in self.id_features])

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
