import logging
import os
from typing import List
from peewee import fn
import peewee as p
from time import time

from server.orders import Orders
import server.production as prod
from server.movements import movement_phase
from server.report import Report
from server.report import distribute_reports
from server.data import Player, db, kv
from server.sbc_parameters import *
from server.research import upgrade_tech
from server import data
from server.newturn import NewTurn

# logging
logger = logging.getLogger("sbc")


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
    data.kv["game_turn"] += 1

    # retrieving orders
    start = time()
    for dirpath, dirnames, orders_files in os.walk(tmp_folder + "/orders"):
        break
    logger.debug(f"{LOG_LEVEL(2)}{len(orders_files)} orders files found")

    # parsing orders
    new_turns = []
    for file in orders_files:
        orders = Orders(dirpath + "/" + file)
        player = Player.get(fn.LOWER(Player.name) == orders.player_name)
        new_turns.append(NewTurn(player, orders))
    stop = time()
    logger.debug(f"{LOG_LEVEL(2)}# Timing # orders retrieving and parsing in {(stop - start) * 1000:.1f} ms")

    # executing orders, game stage by game stage
    # production phase - all players one after the other
    logger.debug(f"{LOG_LEVEL(2)}Production phase")
    start = time()
    for new_turn in new_turns:
        new_turn.production_phase()
    stop = time()
    logger.debug(f"{LOG_LEVEL(2)}# Timing # Production phase in {(stop - start) * 1000:.1f} ms")

    # movement phase - all players one after the other
    start = time()
    logger.debug(f"{LOG_LEVEL(2)}Movement phase")
    for new_turn in new_turns:
        new_turn.movement_phase()
    stop = time()
    logger.debug(f"{LOG_LEVEL(2)}# Timing # Movement phase in {(stop - start) * 1000:.1f} ms")

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
    for new_turn in new_turns:
        new_turn.report.generate_status_report()
        reports[new_turn.player] = new_turn.report

    # send reports to players
    logger.debug(f"{LOG_LEVEL(2)}Report distribution")
    distribute_reports(reports, tmp_folder, channel="file-yaml")  # DEBUG
    stop = time()
    logger.debug(f"{LOG_LEVEL(2)}# Timing # Reports creation and distribution in {(stop - start) * 1000:.1f} ms")

