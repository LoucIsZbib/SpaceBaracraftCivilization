from server.data import Player, Colony, Planet
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

def generate_initial_reports(players):
    """
    A report contains
    a description of star system where the player has a colony/ship
    a description of the colonies of the player
    """
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
        - TODO : dict (python object for high speed simulation like genetic algo)
        - TODO : email
        - TODO : file-human-readable
    """
    for player, report in reports.items():
        if channel == "file-json":
            report.to_json_file(tmp_folder)
        elif channel == "file-yaml":
            report.to_yaml_file(tmp_folder)

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
        self.turn = data.kv["game_turn"]

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
        return {
            "turn": self.turn,
            "player_status": self.player_status,
            "colonies_status": self.colonies_status,
            "galaxy_status": self.galaxis_status,
            "ships_status": self.ships_status
        }

    def evaluate_ship_status(self):
        # TODO : restrain to visible ships
        status = []
        all_ships = data.Ship.select()
        for ship in all_ships:
            status.append(ship.to_dict())
        return status

    def evaluate_player_status(self):
        return {
            "EU": self.player.EU,
            "technologies":
                {"bio": self.player.bio,
                 "meca": self.player.meca,
                 "gv": self.player.gv
                 }
        }

    def evaluate_colonies_status(self):
        status = []
        for colony in self.player.colonies:
            colony_status = colony.to_dict()
            colony_status["food_production"] = prod.food_production(colony)
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
        get visible stars and associate planets IF they have been scanned/seen ?
        """
        visible_stars = self.find_visible_stars()

        status = []
        for star in visible_stars:
            # export visible stars
            star_dict = star.to_dict()

            # export visible planets
            # TODO : retrain to only visited star system
            star_dict["planets"] = []
            for planet in star.planets:
                planet_dict = planet.to_dict()
                planet_dict["food_factor"] = food_planet_factor(planet, self.player)
                planet_dict["meca_factor"] = parts_planet_factor(planet, self.player)
                planet_dict["max_food_prod"], planet_dict["max_wf"] = prod.find_max_food_production(planet, self.player)
                planet_dict["max_parts_prod"], planet_dict["max_ro"] = prod.find_max_parts_production(planet, self.player)
                star_dict["planets"].append(planet_dict)

            status.append(star_dict)

        return status

    def find_visible_stars(self):
        """
        Get visible stars (war fog) from position where I am (colonies, ships)
        """
        coords_where_I_am = set()
        # positions of my colonies
        colonies_cases = (data.Case.select().join(data.Star).join(data.Planet).join(Colony)
                          .where(data.Colony.player == self.player)
                          .where(data.Planet.id == data.Colony.planet)
                          .where(data.Star.id == data.Planet.star)
                          .where(data.Case.id == data.Star.case)
                          .group_by(data.Case)
                          )

        # positions of my ships
        ships_cases = (data.Case.select().join(data.Ship)
                       .where(data.Ship.player == self.player)
                       .group_by(data.Case)
                       )
        for case in colonies_cases:
            coords_where_I_am.add((case.x, case.y, case.z))
        for case in ships_cases:
            coords_where_I_am.add((case.x, case.y, case.z))

        # get star within the visibility range
        all_stars = list(
            data.Star.select(data.Case.x, data.Case.y, data.Case.z, data.Star).join(data.Case)
        )
        all_stars_coords = [[star.case.x, star.case.y, star.case.z] for star in all_stars]

        # calculate distances
        array_me = np.array([[x, y, z] for x, y, z in coords_where_I_am])
        array_stars = np.array(all_stars_coords)
        distances = cdist(array_me, array_stars, "euclidean")

        # evaluate visbility matrix
        # visible_matrix = np.where(distances < VISIBILITY_RANGE)[1]  # problem, gives us 2D array becasue input is 2D
        visible_matrix = np.flatnonzero(distances < VISIBILITY_RANGE)  # same as previous, but in 1D

        # retrieve list of visible Case
        visible_stars = set()
        for i in visible_matrix:
            visible_stars.add(all_stars[i])

        return visible_stars

    def to_yaml_file(self, tmp_folder: str):
        with open(f"{tmp_folder}/report.{self.player.name}.T{self.turn}.YML", "w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f)  # version with python parser of yaml lib --> slow
            # CDumper(self.to_dict(), f)  # ne marche pas, fichier vide, manque un paquet ?

    def to_json_file(self, tmp_folder: str):
        with open(f"{tmp_folder}/report.{self.player.name}.T{self.turn}.JSON", "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)
