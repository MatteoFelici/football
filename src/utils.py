import os
import numpy as np


def get_key(key_file='~/rapidapi-key.txt'):
    with open(os.path.expanduser(key_file), 'r') as f:
        key = f.read().replace('\n', '')

    return key


def safe_num_cast(num: str) -> float:
    try:
        num = np.float(num)
        return num
    except:
        return np.nan
