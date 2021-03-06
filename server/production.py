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
from typing import List

from server.data import db, Planet, Player, Colony

import logging

# logging
logger = logging.getLogger("sbc")

NUMBA_WARNINGS = 0

# STANDARD GAME SETTINGS
OPTIMAL_TEMP_BIOLOGICAL = 25        # optimal temperature in °C for biological species
OPTIMAL_RH_BIOLOGICAL = 100         # optimal Humidity in % RH for biological species
OPTIMAL_TEMP_MECA = -50             # optimal temperature in °C for mechanical species
OPTIMAL_RH_MECA = 0                 # optimal Humidity in % RH for mechanical species
BASE_STD_TEMP = 20                  # base standard deviation for temperature adaptation (gaussian law, std)
BASE_STD_RH = 10                    # base standard deviation for Humidity adaptation (gaussian law, std)
POP_THRESHOLD = 2000                # Factor of max pop size in a colony
BASE_MAINTENANCE_WF = 1             # base cost of maintenance for 1 WF
BASE_MAINTENANCE_RO = 3             # base cost of maintenance for 1 WF or 1 RO
BASE_PRODUCTIVITY = 2               # base food/spare-parts generation per WF or RO


def food_planet_factor(planet: Planet, player: Player):
    """ Compute the factor of BIOLOGICAL productivity relative to planet environment and player attributes """
    temperature_factor = gauss_factor(planet.temperature, OPTIMAL_TEMP_BIOLOGICAL, BASE_STD_TEMP + player.bio)
    humidity_factor = gauss_factor(planet.humidity, OPTIMAL_RH_BIOLOGICAL, BASE_STD_RH + player.bio)
    return temperature_factor * humidity_factor

def meca_planet_factor(planet: Planet, player: Player):
    """ Compute the factor of MECHANICAL maintenance relative to planet environment and player attributes """
    temperature_factor = gauss_factor(planet.temperature, OPTIMAL_TEMP_MECA, BASE_STD_TEMP + player.meca)
    humidity_factor = gauss_factor(planet.humidity, OPTIMAL_RH_MECA, BASE_STD_RH + player.meca)
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

def meca_production(colony: Colony):
    """ Compute spare-parts balance for a colony (owned by a player) """
    spare_parts_created = BASE_PRODUCTIVITY * colony.RO * math.exp(-colony.RO/POP_THRESHOLD)
    spare_parts_maintenance = BASE_MAINTENANCE_RO * colony.RO * (1 - meca_planet_factor(colony.planet, colony.player))
    spare_parts_balance = spare_parts_created - spare_parts_maintenance
    return spare_parts_balance

