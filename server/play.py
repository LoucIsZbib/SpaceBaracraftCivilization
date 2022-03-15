import logging
import os
from typing import List
from time import time
from dataclasses import dataclass

from server.orders import Orders
from server.production import production_phase
from server.movements import movement_phase
from server.report import Report
from server.report import distribute_reports
from server.data import Player, GameData, Ship, Colony, Star
# from server.sbc_parameters import *
import server.sbc_parameters as sbc
from server.sbc_parameters import LOG_LEVEL
from server.research import upgrade_tech
from server import data
# from server.newturn import NewTurn

# logging
logger = logging.getLogger("sbc")


@dataclass
class TurnData:
    player: Player
    orders: Orders
    report: Report


def play_one_turn(game_name: str, tmp_folder: str):
    """
    Turn steps :
    1- retrieve orders (files) from players
        place the orders in tmp_folder/orders
    2- parsing orders
        then rm the orders OR archive them
    3- execute orders from game stage by game stage and prepare reports
    4- send reports
        then rm the reports OR archive them

    """
    logger.info(f"{LOG_LEVEL(1)}-- Game engine running for a new turn --")
    # new turn
    GameData().turn += 1
    turn_data = []  # key is a player, data is TurnData

    # retrieving orders
    start = time()
    for dirpath, dirnames, orders_files in os.walk(tmp_folder + "/orders"):
        break
    logger.debug(f"{LOG_LEVEL(2)}{len(orders_files)} orders files found")

    # parsing orders
    new_turns = []
    for file in orders_files:
        orders = Orders(dirpath + "/" + file)
        player = Player(orders.player_name)
        turn_data.append(TurnData(player, orders, Report(player)))
        # archive orders files
        os.rename(f"{dirpath}/{file}", f"{dirpath}/archive/{file}")
    stop = time()
    logger.debug(f"{LOG_LEVEL(2)}# Timing # orders retrieving and parsing in {(stop - start) * 1000:.1f} ms")

    # executing orders, game stage by game stage
    # production phase - all players one after the other
    logger.debug(f"{LOG_LEVEL(2)}Production phase")
    start = time()
    for donnees in turn_data:
        production_phase(donnees.player, donnees.orders, donnees.report)
    stop = time()
    logger.debug(f"{LOG_LEVEL(2)}# Timing # Production phase in {(stop - start) * 1000:.1f} ms")

    # movement phase - all players one after the other
    start = time()
    logger.debug(f"{LOG_LEVEL(2)}Movement phase")
    for donnees in turn_data:
        movement_phase(donnees.player, donnees.orders, donnees.report)
    stop = time()
    logger.debug(f"{LOG_LEVEL(2)}# Timing # Movement phase in {(stop - start) * 1000:.1f} ms")

    # update fogwar vision
    start = time()
    Star.update_visited(GameData().turn)
    GameData().update_colonies_memory()
    stop = time()
    logger.debug(f"{LOG_LEVEL(2)}# Timing # Update visited in {(stop - start) * 1000:.1f} ms")

    # Combat phase - everyone together
    # TODO : implement combat system
    logger.debug(f"{LOG_LEVEL(2)}Combat phase")
    start = time()

    stop = time()
    logger.debug(f"{LOG_LEVEL(2)}# Timing # Combat phase in {(stop - start) * 1000:.1f} ms")

    # generate reports for each players
    logger.debug(f"{LOG_LEVEL(2)}Reports generation")
    start = time()
    reports = {}
    for donnees in turn_data:
        donnees.report.generate_status_report()
        reports[donnees.player] = donnees.report
    stop = time()
    logger.debug(f"{LOG_LEVEL(2)}# Timing # Reports creation in {(stop - start) * 1000:.1f} ms")

    # send reports to players
    logger.debug(f"{LOG_LEVEL(2)}Report distribution")
    start = time()
    # distribute_reports(reports, tmp_folder, channel="file-yaml")  # DEBUG
    distribute_reports(reports, tmp_folder, channel="file-json")  # DEBUG
    stop = time()
    logger.debug(f"{LOG_LEVEL(2)}# Timing # Reports distribution in {(stop - start) * 1000:.1f} ms")






