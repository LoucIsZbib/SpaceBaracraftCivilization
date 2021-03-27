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
from server.data import Player, GameData, Ship, Position, Colony, Star, Planet
from server.sbc_parameters import *
import server.sbc_parameters as sbc
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

    def execute_action(self, command: List[str]):
        """ This method assign a method to the command in order to perform the needed action, when it needs to be done """

        # --  PARSING ACTION FROM STRING --
        action = None
        cmd = command[0]

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
        elif cmd == "name":
            action = NewTurn.aassign_name

        # Combat
        elif cmd == "attack":
            # TODO: imagining the combat system in order to handle simultaneity
            action = "combat"

        # logger.debug(f"{LOG_LEVEL(5)}'{cmd}' --> {action}")  # DEBUG if problem only, too ugly otherwise

        # -- EXECUTING ACTION --
        action(self, command[1:])

    def production_phase(self):
        """
        handle production phase for a player
        1- ressources gathering (including maintenance costs)
        2- ordres execution
        """
        logger.debug(f"{LOG_LEVEL(3)}Player {self.player.name}")
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
                self.execute_action(command)

    def movement_phase(self):
        # orders execution for the movement phase for this player
        for command in self.orders.move_cmd:
            logger.debug(f"{LOG_LEVEL(5)}cmd: {command}")
            self.execute_action(command)

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
        if currency_type == sbc.EU:
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
        if what == sbc.WF:
            qty_available = self.check_if_ressources_are_available(qty_requested, COST_WF, FOOD)
            cost = int(qty_available*COST_WF)
            self.current_colony.WF += qty_available
            self.report.record_prod(f"{qty_available} WF trained (cost={cost})", 5)

        # Train new RO
        elif what == sbc.RO:
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

    def assign_name(self, arguments: List[str]):
        """
            assign a name to star system -and its planets and futures colonies-

            NAME X Y Z Earth
            arguments = ["X", "Y", "Z", "Earth"]

        """
        # parse data    TODO : check syntax ?
        x = int(arguments[0])
        y = int(arguments[1])
        z = int(arguments[2])
        position = Position(x, y, z)
        name = arguments[3]

        # check if the player is at this position
        present = False
        for ship in position.ships:
            if ship.player == self.player:
                present = True
                break
        if not present:
            self.report.record_prod(f"you are not in {x} {y} {z}, can't assign a name to the star", 5)
            return

        # check if there is a star at these coords
        if position not in Star.stars:
            self.report.record_prod(f"there is no star in {x} {y} {z}", 5)
            return

        # check if it already has a name
        star = Star(position)
        if star.name:
            self.report.record_prod(f"Star in {x} {y} {z} already has a name : {star.name}", 5)
            return

        # now we an give the name to the star
        star.name = name
        self.report.record_prod(f"star in {x} {y} {z} is now called {star.name}", 5)

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
            if (name, self.player) in Ship.ships:
                # it already exists !
                # TODO : re-credit money
                self.report.record_prod(f"Error : ship name {name} is probably a duplicate", 5)
                logger.error(f"ship name duplicate ? (player:{self.player.name}, ship_name: {name})")
            else:
                # it doesn't exist, create it
                Ship(name=name,
                     player=self.player,
                     size=size,
                     type=ship_type,
                     position=self.current_colony.planet.star.position
                     )
                self.report.record_prod(f"Ship {ship_type}{size} {name} has been build", 5)
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
        # TODO : check if arguments are as expected
        # for example BF instead of BF1

        # Ship concerned
        ship_type, ship_size, ship_name = Ship.parse_ship(arguments[:2])
        if not Ship.exists(ship_name, self.player):
            # ship doesn't exists !
            self.report.record_mov(f"{ship_name} doesn't exist for player {self.player.name}")
            return

        # ship exists
        ship = Ship(ship_name, self.player)

        # Destination concerned
        destination = arguments[2:]
        if destination[0].isnumeric():
            # we try to jump to X Y Z coords
            # destination = ["10", "8", "12"]
            x = int(destination[0])
            y = int(destination[1])
            z = int(destination[2])

            # Retrieve corresponding position
            destination_position = Position(x, y, z)
            jump_success = movements.jump(self.player, ship, destination_position)

        else:
            # destination formalism is 'PL Earth'
            # destination = ["PL", "Earth"]
            planet_name = destination[1]

            # retrieve the position where is the planet according to the naming of this player
            # destination_position = Planet.planets[]   # TODO : recover Planet from its name
            # jump_success = movements.jump(self.player, ship, destination_position)
            jump_success = False

        if jump_success:
            self.report.record_mov(f"{ship_type}{ship_size} {ship_name} successfully jumped to {destination}", 5)
        else:
            self.report.record_mov(f"{ship_type}{ship_size} {ship_name} failed to jump to {destination}", 5)
