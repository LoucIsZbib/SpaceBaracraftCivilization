from bot import Bot
from server import newgame, play_one_turn
from server.sbc_parameters import LOG_LEVEL

import random
import string
import os
import yaml
import json
import logging
from time import time

def get_report(player_name: str, working_folder: str, turn: int):
    # JSON
    with open(f"{working_folder}/report.{player_name}.T{turn}.JSON", "r", encoding='utf-8') as f:
        report = json.load(f)

    # YAML
    # with open(f"{working_folder}/report.{player_name}.T{turn}.YML", "r", encoding='utf-8') as f:
    #     report = yaml.safe_load(f)

    return report


if __name__ == "__main__":

    logger = logging.getLogger("sbc")
    # logger.setLevel(level=logging.INFO)
    logger.setLevel(level=logging.DEBUG)
    console_log = logging.StreamHandler()
    logger.addHandler(console_log)

    logger.info(f"{LOG_LEVEL(0)}=== AUTOGAME starting ===")

    # init game settings
    game_folder = '/dev/shm/sbc-' + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    logger.info(f"{LOG_LEVEL(0)}Temporary folder for this game will be {game_folder}")
    os.makedirs(game_folder, exist_ok=True)
    os.makedirs(f"{game_folder}/orders/archive")

    # init server
    start = time()
    with open("config.EXAMPLE.yml", "r") as f:
        game_config = yaml.safe_load(f)
    newgame("testing", game_folder, game_config)
    stop = time()
    logger.debug(f"{LOG_LEVEL(1)}# Timing # game creation in {(stop-start)*1000:.1f} ms")

    # init bots
    start = time()
    logger.info(f"{LOG_LEVEL(0)}Creating Bots...")
    bots = []
    for i in range(1, 4):
        # bot 1
        with open(f"bot_config.EXAMPLE{i}.yml", "r") as f:
            bot_config = yaml.safe_load(f)
        bots.append(Bot(bot_config, game_folder))
    stop = time()
    logger.debug(f"{LOG_LEVEL(1)}# Timing # Bots creation in {(stop - start) * 1000:.1f} ms")

    # play some turns
    for turn_nb in range(0, 10):
        logger.info(f"{LOG_LEVEL(0)}--- TURN {turn_nb} ---")
        # bots play
        logger.info(f"{LOG_LEVEL(1)}bots reads report from turn {turn_nb}, make choices and writing orders for turn {turn_nb+1}")
        start = time()
        for bot in bots:
            report = get_report(bot.name, game_folder, turn_nb)
            bot.play_turn(report)
            bot.write_order()
        stop = time()
        logger.debug(f"{LOG_LEVEL(1)}# Timing # Bots playing in {(stop - start) * 1000:.1f} ms")

        # server play one turn
        start = time()
        play_one_turn("testing", game_folder)
        stop = time()
        logger.debug(f"{LOG_LEVEL(1)}# Timing # Game engine running turn {turn_nb} in {(stop - start) * 1000:.1f} ms")

