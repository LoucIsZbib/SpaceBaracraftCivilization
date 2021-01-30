import argparse
import os
import random
import string
import logging

import newgame
import play

SHM_FOLDER = "/dev/shm/"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title="Possible actions")

    # new game
    parser_newgame = subparsers.add_parser("newgame", help="initiate a new game")
    parser_newgame.add_argument("game_name", help="name of the game to create")
    parser_newgame.add_argument("config_file", help="path to config file")
    parser_newgame.add_argument("--tmp", help="Determine temporary working folder, where tmp files will be written. If not given, a temp directory will be choosen automatically")
    parser_newgame.add_argument("--loglevel", type=str, choices=["error", "info", "debug"], help="logging level, default= error. Error are always printed", default="error")
    parser_newgame.add_argument("--logfile", type=str, help="the file to store the logs, default is None : logging is printed & not stored")

    # play a turn
    parser_play = subparsers.add_parser("play", help="play one turn")
    parser_play.add_argument("game_name", help="name of the game to play one turn")
    parser_play.add_argument("--tmp", help="Determine temporary working folder, where tmp files will be written. If not given, a temp directory will be choosen automatically")
    parser_play.add_argument("--loglevel", type=str, choices=["error", "info", "debug"], help="logging level, default= error. Error are always printed", default="error")
    parser_play.add_argument("--logfile", type=str, help="the file to store the logs, default is None : logging is printed & not stored")

    args = parser.parse_args()

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

    # FOLDER TO STORE GAME DATA
    if args.tmp:
        # create it recursively and ignore if already exists
        args.tmp = args.tmp
        os.makedirs(args.tmp, exist_ok=True)
    else:
        # Create a temporary folder
        args.tmp = SHM_FOLDER + 'sbc-'+''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        logger.info(f"Temporary folder for this game will be {args.tmp}")
        os.makedirs(args.tmp, exist_ok=True)

    # WHICH GAME TO RUN ?
    # in case of multiples games played
    # mutligaming using threads for bots's machine learning or genetic optimization :)
    game_name = args.game_name


    # DEBUG
    newgame.newgame(game_name, args.tmp, None)



