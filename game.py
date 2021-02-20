import argparse
import os
import random
import string
import logging
import yaml

from server import play, newgame

SHM_FOLDER = "/dev/shm/"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title="Possible actions", dest="command", required=True)

    # new game
    parser_newgame = subparsers.add_parser("newgame", help="initiate a new game")
    parser_newgame.add_argument("game_name", help="name of the game to create")
    parser_newgame.add_argument("config_file", help="path to config file")
    parser_newgame.add_argument("--tmp", help="Determine game working folder, where tmp files will be written. If not given, a temp directory will be choosen automatically")
    parser_newgame.add_argument("--loglevel", type=str, choices=["error", "info", "debug"], help="logging level, default= error. Error are always printed", default="error")
    parser_newgame.add_argument("--logfile", type=str, help="the file to store the logs, default is None : logging is printed & not stored")

    # play a turn
    parser_play = subparsers.add_parser("play", help="play one turn")
    parser_play.add_argument("game_name", help="name of the game to play one turn")
    parser_play.add_argument("game_folder", help="Determine game folder, where tmp files will be written.")
    parser_play.add_argument("--loglevel", type=str, choices=["error", "info", "debug"], help="logging level, default= error. Error are always printed", default="error")
    parser_play.add_argument("--logfile", type=str, help="the file to store the logs, default is None : logging is printed & not stored")

    args = parser.parse_args()

    # --- GLOBAL/SHARED FLAGS ---

    # LOGGING
    logger = logging.getLogger("sbc")
    console_log = logging.StreamHandler()
    logger.addHandler(console_log)

    if args.logfile:
        file_log_handler = logging.FileHandler(filename=args.logfile)
        logger.addHandler(file_log_handler)

    if args.loglevel == "error":
        logger.setLevel(level=logging.ERROR)
    elif args.loglevel == "info":
        logger.setLevel(level=logging.INFO)
    elif args.loglevel == "debug":
        logger.setLevel(level=logging.DEBUG)

    # --- NEW GAME FLAGS ---
    if args.command == "newgame":
        # FOLDER TO STORE GAME DATA
        if args.tmp:
            # create it recursively and ignore if already exists
            args.tmp = args.tmp + '/'
            os.makedirs(args.tmp, exist_ok=True)
        else:
            # Create a temporary folder
            args.tmp = SHM_FOLDER + 'sbc-' + ''.join(
                random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            logger.info(f"Temporary folder for this game will be {args.tmp}")
            os.makedirs(args.tmp, exist_ok=True)

        # CONFIG FILE
        with open("config.EXAMPLE.yml", "r") as f:
            config = yaml.safe_load(f)

        newgame(args.game_name, args.tmp, config)

    # --- NEW GAME FLAGS ---
    elif args.command == "play":
        play.play_one_turn(args.game_name, args.game_folder)





