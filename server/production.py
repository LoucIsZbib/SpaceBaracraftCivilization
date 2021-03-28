"""
This file contains algorithm for the economic part of the game:
- calculation of ressources production
- evaluation of factor influing the ressource production
- estimation of max income for a planet
etc.

Test results with numba :
    utilisation de scipy : 0.300 ms pour un factor
    utilisation de numpy sans numba : 0.010 ou 0.020 ms
    utilisation de numpy + numba sans cache : 300ms la première, 0.0003 / 0.001 ms après
    utilisation de numpy + numba avec cache : 70ms la première, 0.0003 / 0.001 ms après
    --> utiliser numba a du sens si on appelle 230 fois la fonction (scipy)
    --> utiliser numba a du sens si on appelle 3500 fois la fonction (numpy)

    SCIPY timeit sans numba = 0.3008 ms
    NUMPY 1 excution avec numba= 70.6749 ms
    NUMPY timeit avec numba = 0.0003 ms
    NUMPY timeit sans numba = 0.0100 ms
    MATH timeit sans numba = 0.0020 ms
    MATH 1 excution avec numba= 229.2347 ms
    MATH timeit avec numba = 0.0003 ms

"""
# from scipy.stats import norm
# from timeit import timeit
# from time import time
# from numba import jit, njit
# import numpy as np
import math
# from typing import List

from server.data import Planet, Player, Colony
from server.sbc_parameters import *

import logging

# logging
logger = logging.getLogger("sbc")

# TODO : do caching on value computing ?

def food_planet_factor(planet: Planet, player: Player):
    """ Compute the factor of BIOLOGICAL productivity relative to planet environment and player attributes """
    temperature_factor = gauss_factor(planet.temperature, player.prefered_temperature, BASE_STD_TEMP + player.techs["bio"].level)
    humidity_factor = max((planet.humidity + player.techs["bio"].level/2) / 100, 1)
    return temperature_factor * humidity_factor

def parts_planet_factor(planet: Planet, player: Player):
    """ Compute the factor of MECHANICAL maintenance relative to planet environment and player attributes """
    temperature_factor = gauss_factor(planet.temperature, player.prefered_temperature, BASE_STD_TEMP + player.techs["meca"].level)
    humidity_factor = max((100-(planet.humidity + player.techs["meca"].level/2))/100, 1)
    return temperature_factor * humidity_factor

def gauss(x: float, moy: float, std: float):
    return 1/(std*math.sqrt(2*math.pi))*math.exp(-(x-moy)**2/(2*std**2))

def gauss_factor(x: float, moy: float, std: float):
    return gauss(x, moy, std) / gauss(moy, moy, std)

def food_production(colony: Colony):
    """ Compute food balance for a colony (owned by a player) """
    food_created = food_planet_factor(colony.planet, colony.player) * colony.WF * (BASE_MAINTENANCE_WF + BASE_PRODUCTIVITY * math.exp(-colony.WF/POP_THRESHOLD))
    food_maintenance = BASE_MAINTENANCE_WF * colony.WF
    food_balance = food_created - food_maintenance
    return food_balance

def parts_production(colony: Colony):
    """ Compute spare-parts balance for a colony (owned by a player) """
    spare_parts_created = BASE_PRODUCTIVITY * colony.RO * math.exp(-colony.RO/POP_THRESHOLD)
    spare_parts_maintenance = BASE_MAINTENANCE_RO * colony.RO * (1 - parts_planet_factor(colony.planet, colony.player))
    spare_parts_balance = spare_parts_created - spare_parts_maintenance
    return spare_parts_balance

def find_max_food_production(planet: Planet, player: Player):
    """
    Compute the maximum hypothetique food production for a planet for a player
    ATTENTION, copy of algorithm of food production (code duplication)

    Strategy : perform a loop with incrementing WF, store the max net income
    """
    food_factor = food_planet_factor(planet, player)

    # start condition
    wf = 10
    net_income = 0
    max_income = 0

    while net_income >= max_income:
        max_income = net_income
        wf += 10
        food_created = food_factor * wf * (BASE_MAINTENANCE_WF + BASE_PRODUCTIVITY * math.exp(-wf/POP_THRESHOLD))
        food_maintenance = BASE_MAINTENANCE_WF * wf
        net_income = food_created - food_maintenance

    max_wf = wf - 10

    return max_income, max_wf


def find_max_parts_production(planet: Planet, player: Player):
    """
    Compute the maximum hypothetique parts production for a planet for a player
    ATTENTION, copy of algorithm of parts production (code duplication)

    Strategy : perform a loop with incrementing RO, store the max net income
    """
    parts_factor = parts_planet_factor(planet, player)

    # start condition
    ro = 10
    net_income = 0
    max_income = 0

    while net_income >= max_income:
        max_income = net_income
        ro += 10
        spare_parts_created = BASE_PRODUCTIVITY * ro * math.exp(-ro / POP_THRESHOLD)
        spare_parts_maintenance = BASE_MAINTENANCE_RO * ro * (1 - parts_factor)
        net_income = spare_parts_created - spare_parts_maintenance

    max_ro = ro - 10

    return max_income, max_ro
