import re
from typing import List
import server.production as production
import server.movements as movements

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
    """
    def __init__(self, filename: str):
        self.player_name, self.prod_cmd, self.move_cmd, self.combat_cmd = Orders.parsing_file(filename)

    @staticmethod
    def parsing_file(filename: str):
        """ parse a file of orders """
        player = ""
        prod = []
        move = []
        combat = []
        flag = None

        with open(filename, 'r') as f:
            for line in f:
                result = Orders.parsing_line(line)
                if result:
                    if result[0] == "production":
                        # We're creating a dict for each planet, containing id info about the planet, and a list of action/commands
                        colony_commands = []
                        prod.append({"type": result[1], "name": result[2], "commands": colony_commands})
                        flag = colony_commands
                        result = None
                    elif result[0] == "movements":
                        flag = move
                        result = None
                    elif result[0] == "combat":
                        flag = combat
                        result = None
                    elif result[0] == "player":
                        # Saving player's name as str, disabling Command attribution
                        player = result[1]
                        flag = None
                        result = None

                    if result:
                        cmd = Command(result[0], result[1:])
                        flag.append(cmd)
        return player, prod, move, combat

    @staticmethod
    def parsing_line(line: str):
        """
        Steps :
        1- reject comment : split according to # and conserve the left part
        2- lowercase the line
        3- regex split according to whitespace but conserve between quotes "..." or '...'
        """
        line = line.split("#")[0]
        line = line.lower()
        matches = command_split_regex.finditer(line)
        result = []
        for m in matches:
            result.append(m.group().strip("\"'"))
        return result

class Command:
    """ contains cmd name, list of arguments, and an action, a method to perform the order """
    def __init__(self, cmd: str, arguments: List[str]):
        self.cmd = cmd
        self.arguments = arguments

        # assign action depending on command
        self.action = Command.assign_action(cmd)

    @staticmethod
    def assign_action(cmd: str):
        """ This method assign a method to the command in order to perform the needed action, when it needs to be done """
        action = None

        # Production
        if cmd == "build":
            action = production.build
        elif cmd == "research":
            action = production.research

        # Movements
        elif cmd == "jump":
            action = movements.jump

        # Combat
        elif cmd == "attack":
            # TODO: imagining the combat system in order to handle simultaneity
            action = "combat"

        return action



