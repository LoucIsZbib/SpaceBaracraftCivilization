from server.data import Player, Colony, Planet
import server.data as data
from server.production import food_planet_factor, meca_planet_factor

import yaml
import json

def generate_reports(players):
    """
    A report contains
    a description of star system where the player has a colony/ship
    a description of the colonies of the player
    """
    reports = {}
    for player in players:
        reports[player] = Report(player)
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

        self.turn = data.kv["game_turn"]

        self.player_status = self.evaluate_player_status()
        self.colonies_status = self.evaluate_colonies_status()
        self.stars_visible = self.evaluate_stars_visible()

    def to_dict(self):
        return {
            "player_status": self.player_status,
            "colonies_status": self.colonies_status,
            "stars_visible": self.stars_visible
        }

    def evaluate_player_status(self):
        return {
            "wallet": self.player.wallet,
            "technologies":
                {"bio": self.player.tech.bio,
                 "meca": self.player.tech.meca
                 }
        }

    def evaluate_colonies_status(self):
        status = []
        for colony in self.player.colonies:
            colony_status = colony.to_dict()
            colony_status["planet"] = colony.planet.to_dict()
            colony_status["planet"]["food_factor"] = food_planet_factor(colony.planet, self.player)
            colony_status["planet"]["meca_factor"] = meca_planet_factor(colony.planet, self.player)
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
