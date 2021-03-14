from server.data import Player, Colony, Planet
import server.data as data
from server.production import food_planet_factor, parts_planet_factor
import server.production as prod
from server.sbc_parameters import *

import yaml
import json
import logging

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

def distribute_reports(reports: dict, tmp_folder: str, channel: str):
    """ distribute the report, needs a channel :
        - file-json
        - file-yaml
        - TODO : dict (python object for high speed simulation like genetic algo)
        - TODO : email
        - TODO : file-human-readable
    """
    for player, report in reports.items():
        if channel == "file_json":
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
        self.player_status = None
        self.colonies_status = None
        self.stars_visible = None
        # TODO : get ships status

    def generate_status_report(self):
        self.turn = data.kv["game_turn"]

        self.player_status = self.evaluate_player_status()
        self.colonies_status = self.evaluate_colonies_status()
        self.stars_visible = self.evaluate_stars_visible()

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
            "player_status": self.player_status,
            "colonies_status": self.colonies_status,
            "stars_visible": self.stars_visible
        }

    def evaluate_player_status(self):
        return {
            "EU": self.player.EU,
            "technologies":
                {"bio": self.player.bio,
                 "meca": self.player.meca
                 }
        }

    def evaluate_colonies_status(self):
        status = []
        for colony in self.player.colonies:
            colony_status = colony.to_dict()
            colony_status["food_production"] = prod.food_production(colony)
            colony_status["parts_production"] = prod.parts_production(colony)
            colony_status["planet"] = colony.planet.to_dict()
            colony_status["planet"]["food_factor"] = food_planet_factor(colony.planet, self.player)
            colony_status["planet"]["meca_factor"] = parts_planet_factor(colony.planet, self.player)
            colony_status["planet"]["max_food_prod"], colony_status["planet"]["max_wf"] = prod.find_max_food_production(colony.planet, self.player)
            colony_status["planet"]["max_parts_prod"], colony_status["planet"]["max_ro"] = prod.find_max_parts_production(colony.planet, self.player)

            status.append(colony_status)
        return status

    def evaluate_stars_visible(self):
        return None

    def to_yaml_file(self, tmp_folder: str):
        with open(f"{tmp_folder}/report.{self.player.name}.T{self.turn}.YML", "w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f)

    def to_json_file(self, tmp_folder: str):
        with open(f"{tmp_folder}/report.{self.player.name}.T{self.turn}.JSON", "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)
