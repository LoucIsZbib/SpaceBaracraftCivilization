from bot import Bot
from server import newgame, play_one_turn

import random
import string
import os
import yaml


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
    # bot 1
    with open("bot_config.EXAMPLE.yml", "r") as f:
        bot_config = yaml.safe_load(f)
    bots.append(Bot(bot_config, game_folder))
    # bot 2
    with open("bot_config.EXAMPLE2.yml", "r") as f:
        bot_config = yaml.safe_load(f)
    bots.append(Bot(bot_config, game_folder))
    # bot 3
    with open("bot_config.EXAMPLE3.yml", "r") as f:
        bot_config = yaml.safe_load(f)
    bots.append(Bot(bot_config, game_folder))

    # play some turns
    for turn_nb in range(1, 5):
        # bots play
        for bot in bots:
            bot.play_turn()
            bot.write_order()

        # server play one turn