from server.data import Player, Colony, Planet, GameData, Ship, Star
import server.data as data
from server.production import food_planet_factor, parts_planet_factor
import server.production as prod
from server.sbc_parameters import *

import yaml
# from yaml import CDumper  # necessite ymal-cpp ?
import json
import logging
import numpy as np
from scipy.spatial.distance import cdist
from time import time

# logging
logger = logging.getLogger("sbc")

def generate_initial_reports():
    """
    A report contains
    a description of star system where the player has a colony/ship
    a description of the colonies of the player
    """
    players = Player.players.values()
    reports = {}
    for player in players:
        report = Report(player)
        report.generate_status_report()
        reports[player] = report
    return reports

def distribute_reports(reports: dict, tmp_folder: str, channel: str = "file-json"):
    """ distribute the report, needs a channel :
        - file-json
        - file-yaml
        - dict {"Bob" : report_as_dict, "Joe": report_as_dict} (python object for high speed simulation like genetic algo)
        - TODO : email
        - TODO : file-human-readable
    """
    if channel == "file-json":
        for player, report in reports.items():
            report.to_json_file(tmp_folder)
    elif channel == "file-yaml":
        for player, report in reports.items():
            report.to_yaml_file(tmp_folder)
    elif channel == "dict":
        reports_dict = {}
        for player, report in reports.items():
            reports_dict[player.name] = report.to_dict()
        return reports_dict

class Report:
    def __init__(self, player: Player):
        self.player = player

        # initialisation
        self.prod_status = {}
        self.current_prod = None
        self.mov_status = []

        # initialisation for pycharm check
        self.turn = None
        self.galaxis_status = None
        self.player_status = None
        self.colonies_status = None
        self.ships_status = None

    def generate_status_report(self):
        self.turn = GameData().turn

        self.player_status = self.evaluate_player_status()
        self.colonies_status = self.evaluate_colonies_status()
        self.galaxis_status = self.evaluate_galaxy_status()
        self.ships_status = self.evaluate_ship_status()

    def initialize_prod_report(self, colony_name: str):
        self.current_prod = []
        self.prod_status[colony_name] = self.current_prod

    def record_prod(self, msg: str, log_level: int = 0):
        self.current_prod.append(msg)
        logger.debug(f"{LOG_LEVEL(log_level)}{msg}")

    def record_mov(self, msg: str, log_level: int = 0):
        self.mov_status.append(msg)
        logger.debug(f"{LOG_LEVEL(log_level)}{msg}")

    def to_dict(self):
        dictionary = {
            "turn": self.turn,
            "player_status": self.player_status,
            "colonies_status": self.colonies_status,
            "galaxy_status": self.galaxis_status,
            "ships_status": self.ships_status
        }
        return dictionary

    def evaluate_ship_status(self):
        status = []
        keys = set()

        # adding ships from position where I am
        positions = self.positions_where_i_am()
        for position in positions:
            for ship in position.ships:
                index = (ship.name.lower(), ship.player)
                if index not in keys:
                    status.append(ship.to_dict())
                    keys.add(index)

        return status

    def evaluate_player_status(self):
        return {
            "EU": self.player.EU,
            "technologies":
                {"bio": self.player.techs["bio"].level,
                 "meca": self.player.techs["meca"].level,
                 "gv": self.player.techs["gv"].level
                 }
        }

    def evaluate_colonies_status(self):
        status = []
        for colony in self.player.colonies:
            colony_status = colony.to_dict()
            colony_status["food_production"] = prod.food_production(colony)     # TODO : cache this information to avoid computing ?
            colony_status["parts_production"] = prod.parts_production(colony)
            colony_status["planet"] = colony.planet.localisation_to_dict()
            # colony_status["planet"]["food_factor"] = food_planet_factor(colony.planet, self.player)
            # colony_status["planet"]["meca_factor"] = parts_planet_factor(colony.planet, self.player)
            # colony_status["planet"]["max_food_prod"], colony_status["planet"]["max_wf"] = prod.find_max_food_production(colony.planet, self.player)
            # colony_status["planet"]["max_parts_prod"], colony_status["planet"]["max_ro"] = prod.find_max_parts_production(colony.planet, self.player)

            status.append(colony_status)
        return status

    def evaluate_galaxy_status(self):
        """
        get visible stars (and already seen star) and associate planets IF stars have been visited
        """
        status = []

        # update seen status
        visible_stars = self.find_visible_stars()
        for star in visible_stars:
            star.seen_by.add(self.player)

        # update report with all seen stars
        seen_stars = [star for star in Star.stars.values() if self.player in star.seen_by]
        for star in seen_stars:
            # export seen star
            star_dict = star.to_dict()

            # export visible planets around this star
            star_dict["planets"] = []
            if self.player in star.visited_by:
                for planet in star.planets.values():
                    planet_dict = planet.to_dict()
                    planet_dict["food_factor"] = food_planet_factor(planet, self.player)
                    planet_dict["meca_factor"] = parts_planet_factor(planet, self.player)
                    planet_dict["max_food_prod"], planet_dict["max_wf"] = prod.find_max_food_production(planet, self.player)
                    planet_dict["max_parts_prod"], planet_dict["max_ro"] = prod.find_max_parts_production(planet, self.player)
                    star_dict["planets"].append(planet_dict)

            status.append(star_dict)

        return status

    def positions_where_i_am(self):
        pos_where_i_am = set()
        # positions of my colonies
        colonies_positions = [colony.planet.star.position for colony in self.player.colonies]

        # positions of my ships
        ships_positions = [ship.position for ship in self.player.ships]

        # combnination of ships and colonies positions
        for position in colonies_positions:
            pos_where_i_am.add(position)
        for position in ships_positions:
            pos_where_i_am.add(position)

        return pos_where_i_am

    def coords_where_i_am(self):
        pos_where_i_am = self.positions_where_i_am()
        coords_where_i_am = [(position.x, position.y, position.z) for position in pos_where_i_am]

        return coords_where_i_am

    def find_visible_stars(self):
        """
        Get visible stars (war fog) from position where I am (colonies, ships)
        """
        coords_where_i_am = self.coords_where_i_am()

        # get star within the visibility range
        all_stars_dict = Star.stars
        all_stars_coords = [[star.position.x, star.position.y, star.position.z] for star in all_stars_dict.values()]

        # calculate distances           TODO : is it usefull to cache something here ?
        array_me = np.array([[x, y, z] for x, y, z in coords_where_i_am])
        array_stars = np.array(all_stars_coords)
        distances = cdist(array_me, array_stars, "euclidean")

        # evaluate visbility matrix
        visible_matrix = np.where(distances < VISIBILITY_RANGE)[1]  # problem, gives us 2D array becasue input is 2D --> [1] necessary

        # retrieve list of visible position
        visible_stars = set()
        for i in visible_matrix:
            visible_stars.add(list(all_stars_dict.values())[i])

        return visible_stars

    def to_yaml_file(self, tmp_folder: str):
        with open(f"{tmp_folder}/report.{self.player.name}.T{self.turn}.YML", "w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f)  # version with python parser of yaml lib --> slow
            # CDumper(self.to_dict(), f)  # ne marche pas, fichier vide, manque un paquet ?

    def to_json_file(self, tmp_folder: str):
        with open(f"{tmp_folder}/report.{self.player.name}.T{self.turn}.JSON", "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)
