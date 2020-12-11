import os
import json
import datetime
import pandas as pd

from utils import safe_num_cast


def process_directory(json_path: str,
                      process_method,
                      **kwargs) -> pd.DataFrame:
    """
    Given a path to a directory with json files, process each file with a given
    method and store all data into a pandas DataFrame.
    You can pass additional keyword arguments to process method.

    Parameters
    ----------
    json_path: str
        Path to directory with json files
    process_method: func
        Method to process each json read into files

    Returns
    -------
    df: pandas.DataFrame
        Output DataFrame with processed data

    """

    files = os.listdir(json_path)
    tot_files = len(files)

    # Initialize empty dataframe
    df = pd.DataFrame()

    # Iterate on each file and append to DataFrame
    for i, json_file in enumerate(files):
        print(f'{i + 1} / {tot_files} --- {json_file}')
        df = df.append(
            process_file(
                file_path=os.path.join(json_path, json_file),
                process_method=process_method,
                **kwargs
            )
        )

    return df


def process_file(file_path: str,
                 process_method,
                 **kwargs) -> pd.DataFrame:
    """
    Given a path to a player statistics file, process statistics data to a
    pandas DataFrame.
    You can pass additional keyword arguments to process method.

    Parameters
    ----------
    file_path: str
        Path to a json file
    process_method: func
        Method to process json read into file

    Returns
    -------
    players_stats: pandas.DataFrame
        Output DataFrame with processed data
    """

    # Load data into dict
    with open(file_path, 'r') as f:
        json_file = json.load(f)

    # Initialize empty dataframe
    df = pd.DataFrame()

    # Iterate on each json and append to DataFrame
    root = list(json_file)[0]
    for j_orig in json_file[root]:
        df = df.append(
            process_method(j_orig, **kwargs)
        )

    return df


class LeagueData:
    """
    This class encapsulate all the methods to process and analyse league-level
    data
    """

    def __init__(self):
        self.fixture_stats_feat = [
            'Shots on Goal', 'Shots off Goal', 'Total Shots', 'Blocked Shots',
            'Shots insidebox', 'Shots outsidebox', 'Fouls', 'Corner Kicks',
            'Offsides', 'Ball Possession', 'Yellow Cards', 'Red Cards',
            'Goalkeeper Saves', 'Total passes', 'Passes accurate', 'Passes %'
        ]
        self.league_numerical_feat = ['elapsed', 'goalsHomeTeam',
                                      'goalsAwayTeam']
        self.league_info_feat = ['name', 'country']

    def json_to_pandas_league(self,
                              j_fixture: dict) -> pd.DataFrame:
        """
        Return a pandas DataFrame from a fixture info json.

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
        new_j = {x: j_fixture[x] for x in self.league_numerical_feat}
        # League info
        new_j.update(
            {'league_' + x: j_fixture['league'][x]
             for x in self.league_info_feat}
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

    def process_league(self, league_file: str) -> pd.DataFrame:
        """

        Parameters
        ----------
        league_file: str
            Path to league file

        Returns
        -------
        league_data: pandas.DataFrame
            DataFrame with all fixtures info in the given file
        """

        league_data = process_file(file_path=league_file,
                                   process_method=self.json_to_pandas_league)

        return league_data

    def json_to_pandas_fixture_stats(self,
                                     j_fixture: dict) -> pd.DataFrame:
        """
        Return a pandas DataFrame row from a fixture statistics json. The
        structured features are unpacked.

        Parameters
        ----------
        j_fixture: dict
            Input json with fixture statistics

        Returns
        -------
        fixture_row: pandas DataFrame
            Row of a pandas DataFrame with fixture stats data
        """

        # Build a new dictionary with processed data
        # First add home data
        new_j = {'.'.join(['home', feat.replace(' ', '_')]):
                 safe_num_cast(j_fixture[feat]['home'])
                 for feat in self.fixture_stats_feat}
        # Then add away data
        new_j.update({'.'.join(['away', feat.replace(' ', '_')]):
                      safe_num_cast(j_fixture[feat]['away'])
                      for feat in self.fixture_stats_feat})

        fixture_row = pd.DataFrame(new_j, index=[j_fixture['fixture_id']])

        return fixture_row

    def process_fixtures(self, fixtures_path: str) -> pd.DataFrame:
        """

        Parameters
        ----------
        fixtures_path: str
            Path to directory with fixture statistics files

        Returns
        -------
        fixture_data: pandas.DataFrame
            DataFrame with all fixture statistics on the given directory
        """

        files = os.listdir(fixtures_path)
        tot_files = len(files)

        # Initialize empty dataframe
        fixture_data = pd.DataFrame()

        # Iterate on each file and append to DataFrame
        for i, json_file_path in enumerate(files):
            print(f'{i + 1} / {tot_files} --- {json_file_path}')

            with open(os.path.join(fixtures_path, json_file_path), 'r') as f:
                json_file = json.load(f)

            fixture_data = fixture_data.append(
                self.json_to_pandas_fixture_stats(
                    j_fixture=json_file['statistics']
                )
            )

        return fixture_data


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
            Default is ['shots', 'goals', 'passes', 'tackles', 'duels',
            'dribbles', 'fouls', 'cards', 'penalty']
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

    def process_fixture(self, fixture_path: str) -> pd.DataFrame:
        """

        Parameters
        ----------
        fixture_path: str
            Path to directory with player statistics files

        Returns
        -------
        players_data: pandas.DataFrame
            DataFrame with all players statistics on the given directory
        """

        players_data = process_file(
            file_path=fixture_path,
            process_method=self.json_to_pandas_player
        )

        return players_data

    def process_league(self, league_path: str) -> pd.DataFrame:
        """

        Parameters
        ----------
        league_path: str
            Path to league directory with players stats

        Returns
        -------
        league_data: pandas.DataFrame
            DataFrame with all players stats into given directory
        """

        league_data = process_directory(
            json_path=league_path,
            process_method=self.json_to_pandas_player
        )

        return league_data
