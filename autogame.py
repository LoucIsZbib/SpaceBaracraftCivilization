from bot import Bot
from server import newgame, play_one_turn

import random
import string
import os
import yaml

def get_report(player_name: str, working_folder: str, turn: int):
    with open(f"{working_folder}/report.{player_name}.T{turn}.YML", "r", encoding='utf-8') as f:
        report = yaml.safe_load(f)
    return report


if __name__ == "__main__":

    # init game settings
    game_folder = '/dev/shm/sbc-' + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    print(f"Temporary folder for this game will be {game_folder}")
    os.makedirs(game_folder, exist_ok=True)

    # init server
    with open("config.EXAMPLE.yml", "r") as f:
        game_config = yaml.safe_load(f)
    newgame("testing", game_folder, game_config)

    # init bots
    bots = []
    for i in range(1, 4):
        # bot 1
        with open(f"bot_config.EXAMPLE{i}.yml", "r") as f:
            bot_config = yaml.safe_load(f)
        bots.append(Bot(bot_config, game_folder))

    # play some turns
    for turn_nb in range(0, 5):
        # bots play
        for bot in bots:
            report = get_report(bot.name, game_folder, turn_nb)
            bot.play_turn(report)
            bot.write_order()

        # server play one turn
        play_one_turn("testing", game_folder)

