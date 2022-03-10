import logging
from typing import List

from server.orders import Orders
import server.production as prod
from server.report import Report
from server.data import Player, GameData, Ship, Position, Colony, Star, Planet
# from server.sbc_parameters import *
import server.sbc_parameters as sbc
from server.sbc_parameters import FOOD, PARTS, EU
from server.research import upgrade_tech
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
        self.stars_targeted_for_explo = []

    def execute_action(self, command: List[str]):
        """ This method assign a method to the command in order to perform the needed action, when it needs to be done """

        # --  PARSING ACTION FROM STRING --
        action = None
        cmd = command[0].lower()

        # Production
        match cmd:
            case "build":
                action = NewTurn.build
            case "research":
                action = NewTurn.research
            case "sell":
                action = NewTurn.sell

        # Movements
            case "jump":
                action = NewTurn.jump
            case "name":
                action = NewTurn.assign_name
            case "explore":
                action = NewTurn.explore

        # Combat
            case "attack":
                # TODO: imagining the combat system in order to handle simultaneity
                action = "combat"

        # logger.debug(f"{sbc.LOG_LEVEL(5)}'{cmd}' --> {action}")  # DEBUG if problem only, too ugly otherwise

        # -- EXECUTING ACTION --
        action(self, command[1:])

    def production_phase(self):
        """
        handle production phase for a player
        1- ressources gathering (including maintenance costs)
        2- maintenance cost
        3- ordres execution, in the order given by the player (for colony, and for orders within each colony)
        """
        logger.debug(f"{sbc.LOG_LEVEL(3)}Player {self.player.name}")

        # 1 - ressources gathering
        for colony in self.player.colonies:
            logger.debug(f"{sbc.LOG_LEVEL(4)}Colony {colony.name}")
            # initializing production report for this colony
            self.report.initialize_prod_report(colony.name)

            # Ressources gathering (maintenance cost already counted)
            food_prod = prod.food_production(colony)
            colony.food += food_prod
            self.report.record_prod(f"food net income = {food_prod:.1f}", 5)
            parts_prod = prod.parts_production(colony)
            colony.parts += parts_prod
            self.report.record_prod(f"parts net income = {parts_prod:.1f}", 5)

        # 2 - mainteance cost
            # TODO : intégrer les coûts de maintenance des vaisseaux et autres

        # 3 - orders executions
        for colony_name, ordres in self.orders.prod_cmd.items():
            self.current_colony = Colony(colony_name)
            # orders execution for this colony
            for command in ordres:
                logger.debug(f"{sbc.LOG_LEVEL(5)}cmd: {command}")
                self.execute_action(command)

    def movement_phase(self):
        # orders execution for the movement phase for this player
        for command in self.orders.move_cmd:
            logger.debug(f"{sbc.LOG_LEVEL(5)}cmd: {command}")
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

    def explore(self, arguments: List[str]):
        """
        Orthographique typique :
            EXPLORE BF1 Firefly
        """
        # Ship concerned
        ship_type, ship_size, ship_name = Ship.parse_ship(arguments[:2])
        if not Ship.exists(ship_name, self.player):
            # ship doesn't exists !
            self.report.record_mov(f"{ship_name} doesn't exist for player {self.player.name}")
            return

        # ship exists
        ship = Ship(ship_name, self.player)

        # destination
        # closest_unvisited_star

        # get the list of unvisited stars
        seen_stars = [star for star in Star.stars.values() if self.player in star.seen_by]

        # sort the list by distance
        stars_sorted_by_distance = sorted(seen_stars, key=lambda s: ship.position.distance_to(s.position))

        # sort by last_visit : the oldest first -- conserve previous sort by distance for egality : if not visited, last visit = turn 0
        stars_sorted = sorted(stars_sorted_by_distance, key=lambda star: star.visited_by.get(self.player, 0))

        # remove explo targets already assigned
        valid_sorted_destination = [star for star in stars_sorted if
                                    star not in self.stars_targeted_for_explo]
        # store this target for future explo ships
        star_destination = valid_sorted_destination[0]
        self.stars_targeted_for_explo.append(star_destination)
        self.report.record_mov(f"Exploration: {ship_name} will jump to {star_destination}", 5)

        # jump
        jump_success = movements.jump(self.player, ship, star_destination.position)

        # logging
        if jump_success:
            self.report.record_mov(f"{ship_type}{ship_size} {ship_name} successfully jumped to {star_destination}", 5)
        else:
            self.report.record_mov(f"{ship_type}{ship_size} {ship_name} failed to jump to {star_destination}", 5)

    def build(self, arguments: List[str]):
        """
        arguments is a list that excludes the command "BUILD"
        BUILD 10 WF --> ["10", "WF"]
        BUILD 50 RO
        BUILD 1 CH2 FireFly
        """
        qty_requested = int(arguments[0])
        what = arguments[1].lower()

        # Train new WF
        if what == sbc.WF:
            qty_available = self.check_if_ressources_are_available(qty_requested, sbc.COST_WF, FOOD)
            cost = int(qty_available * sbc.COST_WF)
            self.current_colony.WF += qty_available
            self.report.record_prod(f"{qty_available} WF trained (cost={cost})", 5)

        # Train new RO
        elif what == sbc.RO:
            qty_available = self.check_if_ressources_are_available(qty_requested, sbc.COST_RO, PARTS)
            cost = int(qty_available * sbc.COST_RO)
            self.current_colony.RO += qty_available
            self.report.record_prod(f"{qty_available} RO trained (cost={cost})", 5)

        # Build new Ship
        elif any(ship_type in what for ship_type in [sbc.BIO_FIGHTER, sbc.BIO_SCOUT, sbc.BIO_CARGO, sbc.MECA_FIGHTER, sbc.MECA_SCOUT, sbc.MECA_CARGO]):
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
            self.report.record_mov(f"you are not in {x} {y} {z}, can't assign a name to the star", 5)
            return

        # check if there is a star at these coords
        if position not in Star.stars:
            self.report.record_mov(f"there is no star in {x} {y} {z}", 5)
            return

        # check if it already has a name
        star = Star(position)
        if star.name:
            self.report.record_mov(f"Star in {x} {y} {z} already has a name : {star.name}", 5)
            return

        # now we an give the name to the star
        star.name = name
        self.report.record_mov(f"star in {x} {y} {z} is now called {star.name}", 5)

    def create_ships(self, ship_type: str, size: int, name: str):
        """ Generic method to create a ship """
        # BIO or MECA ?
        if ship_type in [sbc.BIO_FIGHTER, sbc.BIO_SCOUT, sbc.BIO_CARGO]:
            currency = FOOD
        else:
            currency = PARTS

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
                     ship_type=ship_type,
                     position=self.current_colony.planet.star.position,
                     create=True
                     )
                self.report.record_prod(f"Ship {ship_type}{size} {name} has been build", 5)
        else:
            # Not enough money
            self.report.record_prod(f"Not enough money to build {ship_type}{size}", 5)

    def research(self, arguments: List[str]):
        qty = int(arguments[0])
        tech_str = arguments[1].lower()

        available = self.check_if_ressources_are_available(qty, sbc.COST_RESEARCH, EU)

        level, gain = upgrade_tech(self.player, tech_str, available)
        self.report.record_prod(f"Research investissement of {available} : Tech {tech_str} level is now {level} (+{gain})", 5)

    def sell(self, arguments: List[str]):
        """
        SELL 10 food
        """
        qty = int(arguments[0])
        what = arguments[1]

        available = self.check_if_ressources_are_available(qty, sbc.SELL_TO_GET_EU, what)

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
