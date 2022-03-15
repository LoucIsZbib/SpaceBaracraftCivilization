# import logging
# from typing import List
#
# from server.orders import Orders
# import server.production as prod
# from server.report import Report
# from server.data import Player, GameData, Ship, Position, Colony, Star, Planet
# # from server.sbc_parameters import *
# import server.sbc_parameters as sbc
# from server.sbc_parameters import FOOD, PARTS, EU
# from server.research import upgrade_tech
# from server import movements
#
# # logging
# logger = logging.getLogger("sbc")
#
# class NewTurn:
#     """
#     Class to store data and compute new turn for a player
#     """
#     def __init__(self, player: Player, orders: Orders):
#         self.player = player
#         self.orders = orders
#
#         self.report = Report(player)
#
#
#         self.current_colony = None
#         self.stars_targeted_for_explo = []
#
#     def execute_action(self, command: List[str]):
#         """ This method assign a method to the command in order to perform the needed action, when it needs to be done """
#
#         # --  PARSING ACTION FROM STRING --
#         action = None
#         cmd = command[0].lower()
#
#         # Production
#         match cmd:
#             case "build":
#                 action = NewTurn.build
#             case "research":
#                 action = NewTurn.research
#             case "sell":
#                 action = NewTurn.sell
#
#         # Movements
#             case "jump":
#                 action = NewTurn.jump
#             case "name":
#                 action = NewTurn.assign_name
#             case "explore":
#                 action = NewTurn.explore
#
#         # Combat
#             case "attack":
#                 # TODO: imagining the combat system in order to handle simultaneity
#                 action = "combat"
#
#         # logger.debug(f"{sbc.LOG_LEVEL(5)}'{cmd}' --> {action}")  # DEBUG if problem only, too ugly otherwise
#
#         # -- EXECUTING ACTION --
#         action(self, command[1:])
#
#
