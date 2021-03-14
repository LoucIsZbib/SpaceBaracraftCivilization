import logging
import os
from typing import List
from peewee import fn
import peewee as p
from time import time

from server.orders import Orders
import server.production as prod
from server.report import Report
from server.report import distribute_reports
from server.data import Player, db, kv, Ship, Case, Colony, Star, Planet, PlanetNames
from server.sbc_parameters import *
from server.research import upgrade_tech
from server import data
from server import movements

# logging
logger = logging.getLogger("sbc")

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
                self.report.record_prod(f"food net income = {food_prod:.1f}", 5)
                parts_prod = prod.parts_production(colony)
                colony.parts += parts_prod
                self.report.record_prod(f"parts net income = {parts_prod:.1f}", 5)
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
        with db.atomic():
            # orders execution for this colony
            for command in self.orders.move_cmd:
                logger.debug(f"{LOG_LEVEL(5)}cmd: {command}")
                action = NewTurn.assign_action(command[0])
                action(self, command[1:])

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
                self.report.record_prod(f"{cost} EU requested, {cost_available} only available", 5)
            # 2 - remove spend amount from EU
            self.player.EU -= cost_available
            qty_available = cost_available / price

        elif currency_type == FOOD:
            # 1 - check availability
            if self.current_colony.food >= cost:
                cost_available = cost
            else:
                cost_available = (self.current_colony.food // price) * price
                self.report.record_prod(f"{cost} FOOD requested, {cost_available} only available", 5)
            # 2 - remove spend amount from stock
            self.current_colony.food -= cost_available
            qty_available = cost_available / price

        elif currency_type == PARTS:
            # 1 - check availability
            if self.current_colony.parts >= cost:
                cost_available = cost
            else:
                cost_available = (self.current_colony.parts // price ) * price
                self.report.record_prod(f"{cost} PARTS requested, {cost_available} only available", 5)
            # 2 - remove spend amount from stock
            self.current_colony.parts -= cost_available
            qty_available = cost_available / price

        return int(qty_available)

    def build(self, arguments: List[str]):
        """
        arguments is a list that excludes the command "BUILD"
        BUILD 10 WF --> ["10", "WF"]
        BUILD 50 RO
        BUILD 1 CH2 FireFly
        """
        qty_requested = int(arguments[0])
        what = arguments[1]

        # Train new WF
        if what == WF:
            qty_available = self.check_if_ressources_are_available(qty_requested, COST_WF, FOOD)
            cost = int(qty_available*COST_WF)
            self.current_colony.WF += qty_available
            self.report.record_prod(f"{qty_available} WF trained (cost={cost})", 5)

        # Train new RO
        elif what == RO:
            qty_available = self.check_if_ressources_are_available(qty_requested, COST_RO, PARTS)
            cost = int(qty_available * COST_RO)
            self.current_colony.RO += qty_available
            self.report.record_prod(f"{qty_available} RO trained (cost={cost})", 5)

        # Build new Ship
        elif any(ship_type in what for ship_type in [BIO_FIGHTER, BIO_SCOUT, BIO_CARGO, MECA_FIGHTER, MECA_SCOUT, MECA_CARGO]):
            ship_type, ship_size, ship_name = Ship.parse_ship(arguments[1:])
            self.create_ships(ship_type, ship_size, ship_name)

        else:
            # object unknown
            raise Exception(f"build : unknown object {what}")

    def create_ships(self, ship_type: str, size: int, name: str):
        """ Generic method to create a ship """
        # BIO or MECA ?
        if ship_type in [BIO_FIGHTER, BIO_SCOUT, BIO_CARGO]:
            currency = FOOD
        else:
            currency = PARTS

        # Always 1 ship build per order
        qty_requested = 1

        # Ship cost
        if ship_type in [BIO_FIGHTER, MECA_FIGHTER]:
            ship_cost = size * COST_LEVEL_FIGHTER
        elif ship_type in [BIO_SCOUT, MECA_SCOUT]:
            ship_cost = COST_SCOUT
            size = 1
        elif ship_type in [BIO_CARGO, MECA_CARGO]:
            ship_cost = size * COST_LEVEL_CARGO
        else:
            # Error : ship type unkown
            self.report.record_prod(f"Error : {ship_type} unknown", 5)
            return

        qty_available = self.check_if_ressources_are_available(qty_requested, ship_cost, currency)

        if qty_available > 0:
            # We have money, we can build
            try:
                data.Ship.create(player=self.player,
                                 case=self.current_colony.planet.star.case,
                                 type="CH",
                                 size=size,
                                 name=name)
                self.report.record_prod(f"Ship {ship_type}{size} {name} has been build", 5)
            except p.IntegrityError as e:
                # doublon sur les noms
                self.report.record_prod(f"Error : ship name {name} is probably a duplicate", 5)
                logger.error(f"ship name duplicate ? (player:{self.player.name}, ship_name: {name}), peewee info:\n{e}")
                return
        else:
            # Not enough money
            self.report.record_prod(f"Not enough money to build {ship_type}{size}", 5)

    def research(self, arguments: List[str]):
        qty = int(arguments[0])
        tech_str = arguments[1]

        available = self.check_if_ressources_are_available(qty, COST_RESEARCH, EU)

        level, gain = upgrade_tech(self.player, tech_str, available)
        self.report.record_prod(f"Research investissement of {available} : Tech {tech_str} level is now {level} (+{gain})", 5)

    def sell(self, arguments: List[str]):
        qty = int(arguments[0])
        what = arguments[1]

        available = self.check_if_ressources_are_available(qty, SELL_TO_GET_EU, what)

        self.player.EU += available
        self.report.record_prod(f"Selling {qty} {what.upper()} for {qty} EU", 5)

    def jump(self, arguments: List[str]):
        """
        2 formalism accepted :
            JUMP BF2 Firefly X Y Z
            JUMP BF2 Firefly PL Earth
        """

        # Ship concerned
        ship_type, ship_size, ship_name = Ship.parse_ship(arguments[:2])
        ship = Ship.select().join(Player).where(Ship.player == self.player, Ship.name == ship_name)

        # Destination concerned
        destination = arguments[2:]
        if destination[0].isnumeric():
            # we try to jump to X Y Z coords
            # destination = ["10", "8", "12"]
            x = int(destination[0])
            y = int(destination[1])
            z = int(destination[2])

            # Retrieve corresponding case
            case = data.Case.get_or_create(x=x, y=y, z=z)

            jump_success = movements.jump(self.player, ship, case)

        else:
            # destination formalism is 'PL Earth'
            # destination = ["PL", "Earth"]
            planet_name = destination[1]

            # retrieve the case where is the planet according to the naming of this player
            case = Case.select().join(Star).join(Planet).join(PlanetNames).join(Player).where(
                PlanetNames.player == self.player,
            )

            jump_success = movements.jump(self.player, ship, case)

        if jump_success:
            self.report.record_mov(f"{ship_type}{ship_size} {ship_name} successfully jumped to {destination}")
        else:
            self.report.record_mov(f"{ship_type}{ship_size} {ship_name} failed to jump to {destination}")