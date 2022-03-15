from server.data import Planet, Player, Ship, Position
# from server.sbc_parameters import *
import server.sbc_parameters as sbc
from server.data import Planet, Player, Colony, Ship, Star
from server.orders import Orders
from server.report import Report

import math
import random
from typing import List
import logging

# logging
logger = logging.getLogger("sbc")


def jump(player: Player, ship: Ship, destination: Position):
    """ success_chance is in % """
    distance = ship.position.distance_to(destination)

    success_chance = 100 * math.exp(-distance / (sbc.JUMP_SAFE_DISTANCE + player.techs['gv'].level))
    lottery = random.uniform(0, 100)

    if lottery < success_chance:
        # jump is a success
        ship.position = destination
        jump_success = True

    else:
        # jump is fail
        # jumping somewhere between origin and destination
        x = random.randint(min(ship.position.x, destination.x), max(ship.position.x, destination.x))
        y = random.randint(min(ship.position.y, destination.y), max(ship.position.y, destination.y))
        z = random.randint(min(ship.position.z, destination.z), max(ship.position.z, destination.z))
        ship.position = Position(x, y, z)
        jump_success = False

    return jump_success


def movement_phase(player: Player, orders: Orders, report: Report):
    """ orders execution for the movement phase for this player """

    # se souvenir des systèmes visés pour l'explo pour empecher 2 vaisseaux d'aller explorer le même
    stars_targeted_for_explo = []

    for cmd, *cmd_arguments in orders.move_cmd:
        logger.debug(f"{sbc.LOG_LEVEL(5)}cmd: {cmd}")

        cmd = cmd.lower()
        match cmd:
            case "jump":
                jump_cmd(cmd_arguments, player, report)
            case "name":
                assign_name(cmd_arguments, player, report)
            case "explore":
                explore(cmd_arguments, stars_targeted_for_explo, player, report)


def explore(arguments: List[str], stars_targeted_for_explo: List[Star], player: Player, report: Report):
    """
    Orthographique typique :
        EXPLORE BF1 Firefly
    """
    # Ship concerned
    ship_type, ship_size, ship_name = Ship.parse_ship(arguments[:2])
    if not Ship.exists(ship_name, player):
        # ship doesn't exists !
        report.record_mov(f"{ship_name} doesn't exist for player {player.name}")
        return

    # ship exists, so get it
    ship = Ship(ship_name, player)

    # destination
    # closest_unvisited_star

    # get the list of unvisited stars
    seen_stars = [star for star in Star.stars.values() if player in star.seen_by]

    # sort the list by distance
    stars_sorted_by_distance = sorted(seen_stars, key=lambda s: ship.position.distance_to(s.position))

    # sort by last_visit : the oldest first -- conserve previous sort by distance for egality : if not visited, last visit = turn 0
    stars_sorted = sorted(stars_sorted_by_distance, key=lambda star: star.visited_by.get(player, 0))

    # remove explo targets already assigned
    valid_sorted_destination = [star for star in stars_sorted if
                                star not in stars_targeted_for_explo]
    # store this target for future explo ships
    star_destination = valid_sorted_destination[0]  # TODO : gérer le cas où la liste est vide et xxx[0] n'existe pas
    stars_targeted_for_explo.append(star_destination)
    report.record_mov(f"Exploration: {ship_name} will jump to {star_destination}", 5)

    # jump
    jump_success = jump(player, ship, star_destination.position)

    # logging
    if jump_success:
        report.record_mov(f"{ship_type}{ship_size} {ship_name} successfully jumped to {star_destination}", 5)
    else:
        report.record_mov(f"{ship_type}{ship_size} {ship_name} failed to jump to {star_destination}", 5)


def assign_name(arguments: List[str], player: Player, report: Report):
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
        if ship.player == player:
            present = True
            break
    if not present:
        report.record_mov(f"you are not in {x} {y} {z}, can't assign a name to the star", 5)
        return

    # check if there is a star at these coords
    if position not in Star.stars:
        report.record_mov(f"there is no star in {x} {y} {z}", 5)
        return

    # check if it already has a name
    star = Star(position)
    if star.name:
        report.record_mov(f"Star in {x} {y} {z} already has a name : {star.name}", 5)
        return

    # now we can give the name to the star
    star.name = name
    report.record_mov(f"star in {x} {y} {z} is now called {star.name}", 5)


def jump_cmd(arguments: List[str], player: Player, report: Report):
    """
    2 formalism accepted :
        JUMP BF2 Firefly X Y Z
        JUMP BF2 Firefly PL Earth
    """
    # TODO : check if arguments are as expected
    # for example BF instead of BF1

    # Ship concerned
    ship_type, ship_size, ship_name = Ship.parse_ship(arguments[:2])
    if not Ship.exists(ship_name, player):
        # ship doesn't exists !
        report.record_mov(f"{ship_name} doesn't exist for player {player.name}")
        return

    # ship exists
    ship = Ship(ship_name, player)

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
        jump_success = jump(player, ship, destination_position)

    else:
        # destination formalism is 'PL Earth'
        # destination = ["PL", "Earth"]
        planet_name = destination[1]

        # retrieve the position where is the planet according to the naming of this player
        # destination_position = Planet.planets[]   # TODO : recover Planet from its name
        # jump_success = movements.jump(self.player, ship, destination_position)
        jump_success = False

    if jump_success:
        report.record_mov(f"{ship_type}{ship_size} {ship_name} successfully jumped to {destination}", 5)
    else:
        report.record_mov(f"{ship_type}{ship_size} {ship_name} failed to jump to {destination}", 5)

