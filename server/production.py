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
from typing import List

from server.data import Planet, Player, Colony, Ship
# from server.sbc_parameters import *
import server.sbc_parameters as sbc
from server.orders import Orders
# from server.report import Report
from server.research import upgrade_tech

import logging

# logging
logger = logging.getLogger("sbc")

# TODO : do caching on value computing ?

def food_planet_factor(planet: Planet, player: Player):
    """ Compute the factor of BIOLOGICAL productivity relative to planet environment and player attributes """
    temperature_factor = gauss_factor(planet.temperature, player.prefered_temperature, sbc.BASE_STD_TEMP + player.techs["bio"].level)
    humidity_factor = max((planet.humidity + player.techs["bio"].level/2) / 100, 1)
    return temperature_factor * humidity_factor

def parts_planet_factor(planet: Planet, player: Player):
    """ Compute the factor of MECHANICAL maintenance relative to planet environment and player attributes """
    temperature_factor = gauss_factor(planet.temperature, player.prefered_temperature, sbc.BASE_STD_TEMP + player.techs["meca"].level)
    humidity_factor = max((100-(planet.humidity + player.techs["meca"].level/2))/100, 1)
    return temperature_factor * humidity_factor

def gauss(x: float, moy: float, std: float):
    return 1/(std*math.sqrt(2*math.pi))*math.exp(-(x-moy)**2/(2*std**2))

def gauss_factor(x: float, moy: float, std: float):
    return gauss(x, moy, std) / gauss(moy, moy, std)

def food_production(colony: Colony):
    """ Compute food balance for a colony (owned by a player) """
    food_created = food_planet_factor(colony.planet, colony.player) * colony.WF * (sbc.BASE_MAINTENANCE_WF + sbc.BASE_PRODUCTIVITY * math.exp(-colony.WF/sbc.POP_THRESHOLD))
    food_maintenance = sbc.BASE_MAINTENANCE_WF * colony.WF
    food_balance = food_created - food_maintenance
    return food_balance

def parts_production(colony: Colony):
    """ Compute spare-parts balance for a colony (owned by a player) """
    spare_parts_created = sbc.BASE_PRODUCTIVITY * colony.RO * math.exp(-colony.RO/sbc.POP_THRESHOLD)
    spare_parts_maintenance = sbc.BASE_MAINTENANCE_RO * colony.RO * (1 - parts_planet_factor(colony.planet, colony.player))
    spare_parts_balance = spare_parts_created - spare_parts_maintenance
    return spare_parts_balance

# TODO : supprimer des doublons de code
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
        food_created = food_factor * wf * (sbc.BASE_MAINTENANCE_WF + sbc.BASE_PRODUCTIVITY * math.exp(-wf/sbc.POP_THRESHOLD))
        food_maintenance = sbc.BASE_MAINTENANCE_WF * wf
        net_income = food_created - food_maintenance

    max_wf = wf - 10

    return max_income, max_wf

# TODO : supprimer des doublons de code
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
        spare_parts_created = sbc.BASE_PRODUCTIVITY * ro * math.exp(-ro / sbc.POP_THRESHOLD)
        spare_parts_maintenance = sbc.BASE_MAINTENANCE_RO * ro * (1 - parts_factor)
        net_income = spare_parts_created - spare_parts_maintenance

    max_ro = ro - 10

    return max_income, max_ro


def production_phase(player: Player, orders: Orders, report):
    """
    handle production phase for a player
    1- ressources gathering (including maintenance costs)
    2- maintenance cost
    3- ordres execution, in the order given by the player (for colony, and for orders within each colony)
    """
    logger.debug(f"{sbc.LOG_LEVEL(3)}Player {player.name}")

    # 1 - ressources gathering
    for colony in player.colonies:
        logger.debug(f"{sbc.LOG_LEVEL(4)}Colony {colony.name}")
        # initializing production report for this colony
        report.initialize_prod_report(colony.name)

        # Ressources gathering (maintenance cost already counted)
        food_prod = food_production(colony)
        colony.food += food_prod
        report.record_prod(f"food net income = {food_prod:.1f}", 5)
        parts_prod = parts_production(colony)
        colony.parts += parts_prod
        report.record_prod(f"parts net income = {parts_prod:.1f}", 5)

    # 2 - mainteance cost
        # TODO : intégrer les coûts de maintenance des vaisseaux et autres

    # 3 - orders executions
    for colony_name, ordres in orders.prod_cmd.items():
        current_colony = Colony(colony_name)
        # orders execution for this colony
        for cmd, *cmd_arguments in ordres:
            logger.debug(f"{sbc.LOG_LEVEL(5)}cmd: {cmd}")

            cmd = cmd.lower()
            match cmd:
                case "build":
                    build(cmd_arguments, current_colony, player, report)
                case "research":
                    research(cmd_arguments, current_colony, player, report)
                case "sell":
                    sell(cmd_arguments, current_colony, player, report)

# TODO : est-il pertinent de rendre cette fonction uniquement calculatoire et déporter ailleurs la dépense ?
def check_if_ressources_are_available( qty: int, price: int, currency_type: str, current_colony: Colony, player: Player, report):
    """
    1- get max available from request
    2- Remove currency from stock/EU

    if currency is EU, first check EU, then perform automatic conversion from food or parts
    """
    # no negative spending
    if qty < 0:
        qty = 0

    cost = qty * price

    qty_available = 0  # How many items could be build/bought
    cost_available = 0  # How much it will cost
    if currency_type == sbc.EU:
        # 1 - check availability
        # check in player EU first
        if player.EU >= cost:
            cost_available = cost
        else:
            # TODO : we need to transform automatically EU from food or parts if not enough EU (?)
            # Currently, we use all available
            cost_available = (player.EU // price) * price
            report.record_prod(f"{cost} EU requested, {cost_available} only available", 5)
        # 2 - remove spend amount from EU
        player.EU -= cost_available
        qty_available = cost_available / price

    elif currency_type == sbc.FOOD:
        # 1 - check availability
        if current_colony.food >= cost:
            cost_available = cost
        else:
            cost_available = (current_colony.food // price) * price
            report.record_prod(f"{cost} FOOD requested, {cost_available} only available", 5)
        # 2 - remove spend amount from stock
        current_colony.food -= cost_available
        qty_available = cost_available / price

    elif currency_type == sbc.PARTS:
        # 1 - check availability
        if current_colony.parts >= cost:
            cost_available = cost
        else:
            cost_available = (current_colony.parts // price) * price
            report.record_prod(f"{cost} PARTS requested, {cost_available} only available", 5)
        # 2 - remove spend amount from stock
        current_colony.parts -= cost_available
        qty_available = cost_available / price

    return int(qty_available)

def build(cmd_arguments: List[str], current_colony: Colony, player: Player, report):
    """
    cmd_arguments is a list that excludes the command "BUILD"
    BUILD 10 WF --> ["10", "WF"]
    BUILD 50 RO
    BUILD 1 CH2 FireFly
    """
    qty_requested = int(cmd_arguments[0])
    what = cmd_arguments[1].lower()

    # Train new WF
    if what == sbc.WF:
        qty_available = check_if_ressources_are_available(qty_requested, sbc.COST_WF, sbc.FOOD, current_colony, player, report)
        cost = int(qty_available * sbc.COST_WF)
        current_colony.WF += qty_available
        report.record_prod(f"{qty_available} WF trained (cost={cost})", 5)

    # Train new RO
    elif what == sbc.RO:
        qty_available = check_if_ressources_are_available(qty_requested, sbc.COST_RO, sbc.PARTS, current_colony, player, report)
        cost = int(qty_available * sbc.COST_RO)
        current_colony.RO += qty_available
        report.record_prod(f"{qty_available} RO trained (cost={cost})", 5)

    # Build new Ship
    elif any(ship_type in what for ship_type in
             [sbc.BIO_FIGHTER, sbc.BIO_SCOUT, sbc.BIO_CARGO, sbc.MECA_FIGHTER, sbc.MECA_SCOUT, sbc.MECA_CARGO]):
        ship_type, ship_size, ship_name = Ship.parse_ship(cmd_arguments[1:])
        create_ships(ship_type, ship_size, ship_name, current_colony, player, report)

    else:
        # object unknown
        raise Exception(f"build : unknown object {what}")

def create_ships(ship_type: str, size: int, name: str, current_colony: Colony, player: Player, report):
    """ Generic method to create a ship """
    # BIO or MECA ?
    if ship_type in [sbc.BIO_FIGHTER, sbc.BIO_SCOUT, sbc.BIO_CARGO]:
        currency = sbc.FOOD
    else:
        currency = sbc.PARTS

    # Always 1 ship build per order
    qty_requested = 1

    # Ship cost
    if ship_type in [sbc.BIO_FIGHTER, sbc.MECA_FIGHTER]:
        ship_cost = size * sbc.COST_LEVEL_FIGHTER
    elif ship_type in [sbc.BIO_SCOUT, sbc.MECA_SCOUT]:
        ship_cost = sbc.COST_SCOUT
        size = 1
    elif ship_type in [sbc.BIO_CARGO, sbc.MECA_CARGO]:
        ship_cost = size * sbc.COST_LEVEL_CARGO
    else:
        # Error : ship type unkown
        report.record_prod(f"Error : {ship_type} unknown", 5)
        return

    qty_available = check_if_ressources_are_available(qty_requested, ship_cost, currency, current_colony, player, report)

    if qty_available > 0:
        # We have money, we can build
        if (name, player) in Ship.ships:
            # it already exists !
            # TODO : re-credit money
            report.record_prod(f"Error : ship name {name} is probably a duplicate", 5)
            logger.error(f"ship name duplicate ? (player:{player.name}, ship_name: {name})")
        else:
            # it doesn't exist, create it
            Ship(name=name,
                 player=player,
                 size=size,
                 ship_type=ship_type,
                 position=current_colony.planet.star.position,
                 create=True
                 )
            report.record_prod(f"Ship {ship_type}{size} {name} has been build", 5)
    else:
        # Not enough money
        report.record_prod(f"Not enough money to build {ship_type}{size}", 5)

def research(cmd_arguments: List[str], current_colony: Colony, player: Player, report):
    qty = int(cmd_arguments[0])
    tech_str = cmd_arguments[1].lower()

    available = check_if_ressources_are_available(qty, sbc.COST_RESEARCH, sbc.EU, current_colony, player, report)

    level, gain = upgrade_tech(player, tech_str, available)
    report.record_prod(
        f"Research investissement of {available} : Tech {tech_str} level is now {level} (+{gain})", 5)

def sell(cmd_arguments: List[str], current_colony: Colony, player: Player, report):
    """
    SELL 10 food
    """
    qty = int(cmd_arguments[0])
    what = cmd_arguments[1]

    available = check_if_ressources_are_available(qty, sbc.SELL_TO_GET_EU, what, current_colony, player, report)

    player.EU += available
    report.record_prod(f"Selling {qty} {what.upper()} for {qty} EU", 5)





