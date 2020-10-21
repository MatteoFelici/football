import os


def get_key(key_file='~/rapidapi-key.txt'):
    with open(os.path.expanduser(key_file), 'r') as f:
        key = f.read().replace('\n', '')

    return key
