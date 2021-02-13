import logging
import os

from orders import Orders

# logging
logger = logging.getLogger("sbc")

def play_one_turn(game_name: str, tmp_folder: str):
    """
    Turn steps :
    1- retrieve orders (files) from players
        place the orders in tmp_folder/orders
    2- parsing orders
        then rm the orders OR archive them
    3- execute orders from game stage by game stage and prepare reports
    4- send reports
        then rm the reports OR archive them

    """
    logger.info(f"play new turn")

    # retrieving orders
    dirpath, dirnames, orders_files = os.walk(tmp_folder + "orders")

    # parsing orders
    orders = [Orders(file) for file in orders_files]

    # executing orders, game stage by game stage
    pass

    # send reports
    pass


