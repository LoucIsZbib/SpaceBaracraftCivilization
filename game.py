import argparse
import newgame
import play

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", help="newgame or play one turn", choices=['newgame', 'play'])
    args = parser.parse_args()

    if args.action == "newgame":
        newgame.newgame()

    elif args.action == "play":
        play.play_one_turn()

