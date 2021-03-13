import logging
import os
from typing import List
from peewee import fn
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


class NewTurn:
    """
    Class to store data and compute new turn for a player
    """
    def __init__(self, player: Player, orders: Orders):
        self.player = player
        self.orders = orders

        self.report = Report(player)
        self.current_colony = None

    @staticmethod
    def assign_action(cmd: str):
        """ This method assign a method to the command in order to perform the needed action, when it needs to be done """
        action = None

        # Production
        if cmd == "build":
            action = NewTurn.build
        elif cmd == "research":
            action = NewTurn.research
        elif cmd == "sell":
            action = NewTurn.sell

        # Movements
        elif cmd == "jump":
            action = NewTurn.jump

        # Combat
        elif cmd == "attack":
            # TODO: imagining the combat system in order to handle simultaneity
            action = "combat"

        # logger.debug(f"{LOG_LEVEL(5)}'{cmd}' --> {action}")  # DEBUG if problem only, too ugly otherwise

        return action

    def production_phase(self):
        """
        handle production phase for a player
        1- ressources gathering (including maintenance costs)
        2- ordres execution
        """
        logger.debug(f"{LOG_LEVEL(3)}Player {self.player.name}")
        with db.atomic():
            for colony in self.player.colonies:
                logger.debug(f"{LOG_LEVEL(4)}Colony {colony.name}")
                # initializing production report for this colony
                self.report.initialize_prod_report(colony.name)

                # Ressources gathering (maintenance cost already counted)
                food_prod = prod.food_production(colony)
                colony.food += food_prod
                self.report.record_prod(f"food net income = {food_prod:.1f}")
                logger.debug(f"{LOG_LEVEL(5)}food net income = {food_prod:.1f}")
                parts_prod = prod.meca_production(colony)
                colony.parts += parts_prod
                self.report.record_prod(f"parts net income = {parts_prod:.1f}")
                logger.debug(f"{LOG_LEVEL(5)}parts net income = {parts_prod:.1f}")
                self.current_colony = colony

                # orders execution for this colony
                for command in self.orders.prod_cmd[colony.name.lower()]:
                    logger.debug(f"{LOG_LEVEL(5)}cmd: {command}")
                    action = NewTurn.assign_action(command[0])
                    action(self, command[1:])

                # saving data
                colony.save()
                self.player.save()

    def movement_phase(self):
        pass

    def check_if_ressources_are_available(self, qty: int, price: int, currency_type: str):
        """
        1- get max available from request
        2- Remove currency from stock/EU

        if currency is EU, first check EU, then perform automatic conversion from food or parts
        """
        # no negative spending
        if qty < 0:
            qty = 0

        cost = qty * price

        qty_available = 0       # How many items could be build/bought
        cost_available = 0      # How much it will cost
        if currency_type == EU:
            # 1 - check availability
            # check in player EU first
            if self.player.EU >= cost:
                cost_available = cost
            else:
                # TODO : we need to transform automatically EU from food or parts if not enough EU (?)
                # Currently, we use all available
                cost_available = (self.player.EU // price ) * price
                self.report.record_prod(f"{cost} EU requested, {cost_available} only available")
                logger.debug(f"{LOG_LEVEL(5)}{cost} EU requested, {cost_available} only available")
            # 2 - remove spend amount from EU
            self.player.EU -= cost_available
            qty_available = cost_available / price

        elif currency_type == FOOD:
            # 1 - check availability
            if self.current_colony.food >= cost:
                cost_available = cost
            else:
                cost_available = (self.current_colony.food // price) * price
                self.report.record_prod(f"{cost} FOOD requested, {cost_available} only available")
                logger.debug(f"{LOG_LEVEL(5)}{cost} FOOD requested, {cost_available} only available")
            # 2 - remove spend amount from stock
            self.current_colony.food -= cost_available
            qty_available = cost_available / price

        elif currency_type == PARTS:
            # 1 - check availability
            if self.current_colony.parts >= cost:
                cost_available = cost
            else:
                cost_available = (self.current_colony.parts // price ) * price
                self.report.record_prod(f"{cost} PARTS requested, {cost_available} only available")
                logger.debug(f"{LOG_LEVEL(5)}{cost} PARTS requested, {cost_available} only available")
            # 2 - remove spend amount from stock
            self.current_colony.parts -= cost_available
            qty_available = cost_available / price

        return int(qty_available)

    def build(self, arguments: List[str]):
        """
        arguments is a list that excludes the command "BUILD"
        BUILD 10 WF --> ["10", "WF"]
        BUILD 50 RO
        """
        qty_requested = int(arguments[0])
        what = arguments[1]

        if what == WF:
            qty_available = self.check_if_ressources_are_available(qty_requested, COST_WF, FOOD)
            cost = int(qty_available*COST_WF)
            self.current_colony.WF += qty_available
            self.report.record_prod(f"{qty_available} WF trained (cost={cost})")
            logger.debug(f"{LOG_LEVEL(5)}{qty_available} WF trained (cost={cost})")

        elif what == RO:
            qty_available = self.check_if_ressources_are_available(qty_requested, COST_RO, PARTS)
            cost = int(qty_available * COST_RO)
            self.current_colony.RO += qty_available
            self.report.record_prod(f"{qty_available} RO trained (cost={cost})")
            logger.debug(f"{LOG_LEVEL(5)}{qty_available} RO trained (cost={cost})")

        else:
            # object unknown
            raise Exception(f"build : unknown object {what}")

    def research(self, arguments: List[str]):
        qty = int(arguments[0])
        tech_str = arguments[1]

        available = self.check_if_ressources_are_available(qty, COST_RESEARCH, EU)

        level, gain = upgrade_tech(self.player, tech_str, available)
        self.report.record_prod(f"Research investissement of {available} : Tech {tech_str} level is now {level} (+{gain})")
        logger.debug(f"{LOG_LEVEL(5)}Research investissement of {available} : Tech {tech_str} level is now {level} (+{gain})")

    def sell(self, arguments: List[str]):
        qty = int(arguments[0])
        what = arguments[1]

        available = self.check_if_ressources_are_available(qty, SELL_TO_GET_EU, what)

        self.player.EU += available
        self.report.record_prod(f"Selling {qty} {what.upper()} for {qty} EU")
        logger.debug(f"{LOG_LEVEL(5)}Selling {qty} {what.upper()} for {qty} EU")

    def jump(self):
        pass

