import re
from typing import List

import logging
# logging
logger = logging.getLogger("sbc")

# command regex pattern
command_split_pattern = r"""[^ \t"'\n]+|"[^"]*"|'[^']*'"""
# command_split_pattern = r"""[^ \t"\n]+|"[^"]*\""""
command_split_regex = re.compile(command_split_pattern)

class Orders:
    """
    Orders object are build for each player,
    it contains list of Command object for each game phase (production, movements, combat)

    for production orders,  Commands are regrouped by planet/colonies in a dict

    12/02/2021 : orders are available on files, formatted under the following spec:
    - each line is a command
    - separator is " " (white space)
    - use double-quotes to get a name including spaces
    - everything on right of # is a comment and is ignored

    data structures for orders :
    orders: Orders
        player_name: str
        prod_cmd: dict, keys are colonies's names
            colony1_name: List of commands
            colony2_name: List of commands
        move_cmd: List
        combat_cmd: List

    """
    def __init__(self, filename: str):
        self.player_name, self.prod_cmd, self.move_cmd, self.combat_cmd = Orders.parsing_file(filename)

    @staticmethod
    def parsing_file(filename: str):
        """ parse a file of orders """
        player_name = ""
        prod = {}
        move = []
        combat = []
        flag = None

        with open(filename, 'r') as f:
            for line in f:
                result = Orders.parsing_line(line)
                if result:
                    if result[0].lower() == "production":
                        # Each colony name is a key of the dict, and data is a list of action/commands
                        colony_commands = []
                        prod[result[2].lower()] = colony_commands
                        flag = colony_commands
                        result = None
                    elif result[0].lower() == "movements":
                        flag = move
                        result = None
                    elif result[0].lower() == "combat":
                        flag = combat
                        result = None
                    elif result[0].lower() == "player":
                        # Saving player's name as str, disabling Command attribution
                        player_name = result[1].lower()
                        flag = None
                        result = None

                    if result:
                        flag.append(result)
        return player_name, prod, move, combat

    @staticmethod
    def parsing_line(line: str):
        """
        Steps :
        1- reject comment : split according to # and conserve the left part
        2- lowercase the line
        3- regex split according to whitespace but conserve between quotes "..." or '...'
        """
        line = line.split("#")[0]
        # line = line.lower()
        matches = command_split_regex.finditer(line)
        result = []
        for m in matches:
            result.append(m.group().strip("\"'"))
        return result






