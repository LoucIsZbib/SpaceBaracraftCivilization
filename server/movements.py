from server.data import Planet, Player, Ship, Position
from server.sbc_parameters import *

import math
import random
from typing import List
import logging

# logging
logger = logging.getLogger("sbc")


def jump(player: Player, ship: Ship, destination: Position):
    """ success_chance is in % """
    distance = ship.position.distance_to(destination)

    success_chance = 100 * math.exp(-distance / (JUMP_SAFE_DISTANCE + player.techs['gv'].level))
    lottery = random.uniform(0, 100)

    if lottery < success_chance:
        # jump is a success
        ship.position = destination
        jump_success = True

    else:
        # jump is fail
        # jumping somewhere between origin and destination
        x = random.randint(min(ship.position.x, destination.x), max(ship.position.x, destination.x))
        y = random.randint(min(ship.position.y, destination.y), max(ship.position.y, destination.y))
        z = random.randint(min(ship.position.z, destination.z), max(ship.position.z, destination.z))
        ship.position = Position(x, y, z)
        jump_success = False

    return jump_success
