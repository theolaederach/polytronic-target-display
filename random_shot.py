import random

def random_shot(num_shots=1):
    """
    Generate a list of random shot coordinates.
    Each coordinate is a tuple (x, y) where x and y are integers between 0 and 1000.
    """
    shots = []
    for _ in range(num_shots):
        x = random.randint(0, 1000)
        y = random.randint(0, 1000)
        shots.append((x, y))
    return shots