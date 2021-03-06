import logging
import os
from typing import List
from peewee import fn

from server.orders import Orders
import server.production as prod
from server.movements import movement_phase
from server.report import Report
from server.report import distribute_reports
from server.data import Player, db, kv
from server.sbc_item_names import EU, FOOD, PARTS
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
    logger.info(f"play new turn")
    # new turn
    data.kv["game_turn"] += 1

    # retrieving orders
    for dirpath, dirnames, orders_files in os.walk(tmp_folder + "/orders"):
        break

    # parsing orders
    new_turns = []
    for file in orders_files:
        orders = Orders(dirpath + "/" + file)
        player = Player.get(fn.LOWER(Player.name) == orders.player_name)
        new_turns.append(NewTurn(player, orders))

    # executing orders, game stage by game stage
    # production phase - all players one after the other
    for new_turn in new_turns:
        new_turn.production_phase()

    # movement phase - all players one after the other
    for new_turn in new_turns:
        new_turn.movement_phase()

    # Combat phase - everyone together
    # TODO : implement combat system

    # generate reports for each players
    reports = {}
    for new_turn in new_turns:
        new_turn.report.generate_status_report()
        reports[new_turn.player] = new_turn.report

    # send reports to players
    distribute_reports(reports, tmp_folder, channel="file-yaml")  # DEBUG


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

        # Movements
        elif cmd == "jump":
            action = NewTurn.jump

        # Combat
        elif cmd == "attack":
            # TODO: imagining the combat system in order to handle simultaneity
            action = "combat"

        return action

    def production_phase(self):
        """
        handle production phase for a player
        1- ressources gathering (including maintenance costs)
        2- ordres execution
        """
        with db.atomic():
            for colony in self.player.colonies:
                # initializing production report for this colony
                self.report.initialize_prod_report(colony.name)

                # Ressources gathering (maintenance cost already counted)
                food_prod = prod.food_production(colony)
                colony.food += food_prod
                self.report.record_prod(f"food net income = {food_prod}")
                parts_prod = prod.meca_production(colony)
                colony.parts += parts_prod
                self.report.record_prod(f"parts net income = {parts_prod}")
                # colony.save()  # test with later saving
                self.current_colony = colony

                # orders execution for this colony
                for command in self.orders.prod_cmd[colony.name]:
                    action = NewTurn.assign_action(command[0])
                    action(self, command[1:])

                colony.save()

    def movement_phase(self):
        pass

    def check_if_ressources_are_available(self, qty: int, currency_type: str):
        """
        1- get max available from request
        2- Remove currency from stock/wallet

        if currency is EU, first check wallet, then perform automatic conversion from food or parts
        """

        available = 0
        if currency_type == EU:
            # 1 - check availability
            # check in player wallet first
            if self.player.wallet >= qty:
                available = qty
            else:
                # TODO : we need to transform EU from food or parts if not enough EU
                # Currently, we use all available
                available = self.player.wallet
                self.report.record_prod(f"{qty} EU requested, {available} only available")

            # 2 - remove spend amount from wallet
            self.player.wallet -= available

        elif currency_type == FOOD:
            # 1 - check availability
            if self.current_colony.food >= qty:
                available = qty
            else:
                available = self.current_colony.food
                self.report.record_prod(f"{qty} FOOD requested, {available} only available")
            # 2 - remove spend amount from stock
            self.current_colony.food -= available

        elif currency_type == PARTS:
            # 1 - check availability
            if self.current_colony.parts >= qty:
                available = qty
            else:
                available = self.current_colony.parts
                self.report.record_prod(f"{qty} PARTS requested, {available} only available")
            # 2 - remove spend amount from stock
            self.current_colony.parts -= available

        return available

    def build(self, arguments: List[str]):
        pass

    def research(self, arguments: List[str]):
        qty = int(arguments[0])
        tech_str = arguments[1]

        available = self.check_if_ressources_are_available(qty, EU)

        level, gain = upgrade_tech(self.player, tech_str, available)
        self.report.record_prod(f"Research investissement of {qty} : Tech {tech_str} level is now {level} (+{gain})")

    def jump(self):
        pass

