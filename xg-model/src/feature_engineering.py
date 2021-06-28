import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


def isInside(x1, y1, x2, y2, x3, y3, x, y):
    """
    Check if point (x, y) is inside of the triangle with vertices
    ((x1, y1), (x2, y2), (x3, y3))
    Parameters
    ----------
    x1, y1, x2, y2, x3, y3: float
        Vertices of the triangle
    x, y: float
        Point to check

    Returns
    -------
    bool - True if point is inside triangle, otherwise False
    """

    a = ((y2 - y3 ) * (x - x3) + (x3 - x2 ) * (y - y3)) / \
                ((y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3))
    b = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / (
                (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3))
    c = 1 - a - b

    if (0 <= a <= 1) and (0 <= b <= 1) and (0 <= c <= 1):
        return True
    else:
        return False


class XGFeatEng(BaseEstimator, TransformerMixin):

    def __init__(self):

        self.pitch_dim = (105, 65)
        self.goal_dim = 7.32

    def _normalize_x(self, x):

        return x * self.pitch_dim[0] / 120

    def _normalize_y(self, y):
        return y * self.pitch_dim[1] / 80

    def _calculate_angle(self, x, y):
        """
        Calculate shot angle
        """

        angle = np.arctan(
            self.goal_dim * (self.pitch_dim[0] - x) /
            ((self.pitch_dim[0] - x) ** 2 + y ** 2 - (self.goal_dim / 2) ** 2)
        )
        # If negative, add pi
        angle[angle < 0] += np.pi

        return angle

    def _calcuate_distance(self, a, b):
        """
        Calculate euclidean distance between two points - vectorized
        """

        return np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    def _check_if_in_goal_cone(self, players_list, x_shot, y_shot):
        """
        Check if player is in goal cone in respect of the shot taken at
        (x_shot, y_shot), for each player in players_list; return list of
        players in cone
        """
        return [
            player for player in players_list
            if isInside(
                x_shot, y_shot,
                # Left goal post
                self.pitch_dim[0], (self.pitch_dim[1] - self.goal_dim / 2),
                # Right goal post
                self.pitch_dim[0], (self.pitch_dim[1] + self.goal_dim / 2),
                self._normalize_x(player['location'][0]),
                self._normalize_y(player['location'][1])
            ) == 1
        ]

    def fit(self, X):
        return self

    def transform(self, X):
        df = X.copy()

        # Transform coordinates to meters
        df['x_shot'] = self._normalize_x(df['x_shot'])
        df['y_shot'] = self._normalize_y(df['y_shot'])

        # Center the y coordinate in respect of the pitch (widht 65)
        df['y_center'] = np.abs(df['y_shot'] - self.pitch_dim[1] / 2)

        # Calculate distance from center of the goal
        df['distance'] = self._calcuate_distance(
            (self.pitch_dim[0], 0), (df['x_shot'], df['y_center'])
        )

        # Angle
        df['angle'] = self._calculate_angle(df['x_shot'], df['y_center'])

        # Check if shot is after key pass
        df['has_key_pass'] = 1
        df.loc[df['key_pass'].isnull(), 'has_key_pass'] = 0

        # Calculate distance from point where the ball is controlled to shot
        df['distance_before_shot'] = self._calcuate_distance(
            (df['x_shot'], df['y_shot']),
            (df['x_pass_received'], df['y_pass_received'])
        )

        # Check if receiving pass is high
        df['is_high_pass'] = 0
        df.loc[df['pass_height'] == 'High Pass', 'is_high_pass'] = 1

        # Working on freeze frame
        # Number of players into the "goal cone"
        df['players_between'] = df.apply(
            lambda x: len(
                self._check_if_in_goal_cone(x['freeze_frame'], x['x_shot'],
                                            x['y_shot'])
            )
            if x['freeze_frame'] is not None else None, 1
        )

        # Number of opponents
        df['opponents_between'] = df.apply(
            lambda x: len(
                self._check_if_in_goal_cone(
                    [i for i in x['freeze_frame'] if not i['teammate']],
                    x['x_shot'], x['y_shot']
                )
            )
            if x['freeze_frame'] is not None else None, 1
        )

        # Is goalkeeper in goal cone
        df['is_there_goalkeeper'] = df.apply(
            lambda x: 1 if len(
                self._check_if_in_goal_cone(
                    [i for i in x['freeze_frame'] if not i['teammate']
                     and i['position']['name'] == 'Goalkeeper'],
                    x['x_shot'], x['y_shot']
                )
            ) > 0 or x['freeze_frame'] is None else 0, 1
        )

        # Distance to nearest opponent
        # Select only opponents in the goal cone
        df['nearest_opponent'] = df.apply(
            lambda x: np.min([
                self._calcuate_distance(
                    (df['x_shot'], df['y_shot']),
                    (self._normalize_x(p['location'][0]),
                     self._normalize_y(p['location'][1]))
                )
                for p in self._check_if_in_goal_cone(
                    [i for i in x['freeze_frame'] if not i['teammate']],
                    x['x_shot'], x['y_shot']
                )
            ])
            if x['freeze_frame'] is not None and x['opponents_between'] > 0
            else None, 1
        )

        # Drop unused features
        return df.drop(['freeze_frame', 'key_pass', 'pass_height',
                        'x_pass_received', 'y_pass_received'], 1)
