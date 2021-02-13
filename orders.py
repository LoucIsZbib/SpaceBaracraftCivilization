import logging
import re
from time import time

from typing import List

# logging
logger = logging.getLogger("sbc")

# command regex pattern
command_split_pattern = r"""[^ \t"'\n]+|"[^"]*"|'[^'"]*'"""
command_split_regex = re.compile(command_split_pattern)

class Orders:
    """
    12/02/2021 : orders are available on files, formatted under the following spec:
    - each line is a command
    - separator is " " (white space)
    - everything on right of # is a comment and is ignored

    """
    def __init__(self, filename: str):
        self.player, self.production, self.movements, self.combat = Orders.parsing_file(filename)

        i = 0

    @staticmethod
    def parsing_file(filename: str):
        """ parse a file of orders """
        player = []
        production = []
        movements = []
        combat = []
        flag = player
        with open(filename, 'r') as f:
            for line in f:
                result = Orders.parsing_line(line)
                if result:
                    if result[0] == "production":
                        flag = production
                        result = result[1:]
                    elif result[0] == "movements":
                        flag = movements
                        result = None
                    elif result[0] == "combat":
                        flag = combat
                        result = None
                    elif result[0] == "player":
                        flag = player
                        result = result[1]

                    if result:
                        flag.append(result)
        return player, production, movements, combat

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
    def __init__(self, cmd: str, arguments: List[str]):
        self.cmd = cmd
        self.arguments = arguments


if __name__ == "__main__":
    file = "orders.EXAMPLE.txt"
    start = time()
    res = Orders.parsing_file(file)
    stop = time()
    print(f"{(stop-start)*1000:.3f} ms -- {res}")

