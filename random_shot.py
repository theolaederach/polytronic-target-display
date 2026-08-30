# Title : Random shots
# Author : theo.laerach
# Last update : 30.08.2026
# Description : function for generate random shot for testing

import random as rdm

def generate(num_shots: int = 1) -> list[tuple[float, float]] :
    """
    Generate a list of random shot coordinates.
    Each coordinate is a tuple (x, y) where x and y are integers between 0 and 1000.
    """
    shots: list[tuple[float, float]] = []

    for _ in range(num_shots):
        x_pos = rdm.randint(-500, 500)
        y_pos = rdm.randint(-500, 500)
        shot_pos = (x_pos/1000, y_pos/1000)
        shots.append(shot_pos)

    return shots
