from server.data import Planet, Player, Ship, Case
from server.sbc_parameters import *

import math
import random
from typing import List
import logging

# logging
logger = logging.getLogger("sbc")


def jump(player: Player, ship: Ship, destination: Case):
    """ success_chance is in % """
    distance = Ship.distance(ship.case, destination)

    success_chance = math.exp(-distance / (JUMP_SAFE_DISTANCE + player.gv))
    lottery = random.uniform(0, 100)

    if lottery < success_chance:
        # jump is a success
        ship.case = destination
        ship.save()
        jump_success = True

    else:
        # jump is fail
        # jumping somewhere between origin and destination
        x = random.randint(min(ship.case.x, destination.x), max(ship.case.x, destination.x))
        y = random.randint(min(ship.case.y, destination.y), max(ship.case.y, destination.y))
        z = random.randint(min(ship.case.z, destination.z), max(ship.case.z, destination.z))
        case = Case.get_or_create(x=x, y=y, z=z)
        ship.case = case
        ship.save()
        jump_success = False

    return jump_success
