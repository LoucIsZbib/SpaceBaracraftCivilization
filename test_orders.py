import pytest
from orders import Orders, Command
import production
import movements

def test_parsing_line():
    msg = """  \t TRANSFER 1 CU PL "Earth d'en bas" TR 'Firefly de la mort' BAS supercool """
    result = Orders.parsing_line(msg)
    solution = ['transfer', "1", "cu", 'pl', "earth d'en bas", "tr", "firefly de la mort", "bas", "supercool"]
    assert solution == result


# Not testable because of Command objects
# def test_parsing_file():
#     content = '''# This is a command, works also within a line : everything on right is ignored
# # First line = name of the Player
# player Flibustiers
#
# # First part = PRODUCTION
# PRODUCTION PL Earth
# build 50 WF
#
# Production PL "Red Mars"
# REsearch 10 bio
#
#
#
#
# # Second part = MOVEMENTS
# MOVEMENTS
# jump FF firefly PL Venus
#
# Orbit DD "ISS barakuda" PL Earth
#
# # Last part = COMBAT
# COMBAT
# attack FF Firefly PL Venus
#
# '''
#     filename = "temporary_file"
#     with open(filename, "w") as f:
#         f.write(content)
#
#     player_name, prod_cmd, move_cmd, combat_cmd = Orders.parsing_file(filename)
#
#     assert player_name == "flibustiers"
#     assert prod_cmd == [
#         {
#             "type": "pl", "name": "earth", "commands": [
#                 Command("build", ["50", "wf"]),
#             ]
#         },
#         {
#             "type": "pl", "name": "red mars", "commands": [
#                 Command('research', ['10', 'bio']),
#             ]
#         }
#     ]
#     assert move_cmd == [
#         Command("jump", ["ff", "firefly", "pl", "venus"]),
#         Command("orbit", ["dd", "iss barakuda", "pl", "earth"])
#     ]
#     assert combat_cmd == [
#         Command("attack", ["ff", "firefly", "pl", "venus"])
#     ]

