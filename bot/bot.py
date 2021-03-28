from bot.names import generate_name
from bot.bot_data import Position, Planet, Player, Colony, Ship, Technologies, Star
import random
from time import time
import os
import json

class Bot:
    def __init__(self, config: dict, game_folder: str):
        self.game_folder = game_folder
        self.name = config["name"]

        # init instance variables
        self.turn = 0
        self.orders = []
        self.report = None
        self.me = None
        self.colonies = {}
        self.planets = []
        self.ships = []
        self.volatile_brain = {
            "explo_targets": []
        }

        # load brain
        self.brain = self.load_brain(config)

    def load_brain(self, config):
        """
        loads bot's brain : history of some actions, intends, behavior..
        behaviors is loaded from config_file each time to allow change of behavior during the game
        """
        # memory of actions, intends
        brain_file = f"{self.game_folder}/bot_brain_{self.name}.json"
        if os.path.exists(brain_file):
            with open(brain_file, "r", encoding="utf8") as f:
                brain = json.load(f)
        else:
            # first time, init the brain
            brain = {
                "visited_stars": set(),
            }

        # behavior
        brain["behavior"] = config["behavior"]

        return brain

    def save_brain(self):
        brain_file = f"{self.game_folder}/bot_brain_{self.name}.json"
        with open(brain_file, "w", encoding="utf8") as f:
            json.dump(self.brain, f, ensure_ascii=False, indent=4)

    def parse_report(self, report: dict):
        """ Parse the orders given in dict format and create objects for easy & quick manipulation """
        self.report = report

        # reset the object memory (class attribute)
        Position.reset()
        Star.reset()
        Planet.reset()
        Player.reset()
        Colony.reset()
        Ship.reset()

        # parsing turn
        current_turn = report["turn"]

        # parsing stars & planets
        for star_status in report["galaxy_status"]:
            # position
            position = Position(star_status["position"]['x'],
                                star_status['position']['y'],
                                star_status['position']['z'])

            # star
            star = Star(position)
            star.name = star_status["name"]

            # planets
            for planet in star_status['planets']:
                p = Planet(star,
                           planet['numero'],
                           temperature=planet['temperature'],
                           humidity=planet["humidity"],
                           max_food_prod=planet["max_food_prod"],
                           max_parts_prod=planet["max_parts_prod"],
                           max_ro=planet["max_ro"],
                           max_wf=planet["max_wf"],
                           food_factor=planet["food_factor"],
                           meca_factor=planet["meca_factor"]
                           )
                self.planets.append(p)
                star.planets[p.numero] = p

        # parsing players
        self.me = Player(self.name)
        self.me.EU = report["player_status"]["EU"]
        self.me.tech = Technologies(report["player_status"]["technologies"]["bio"],
                                    report["player_status"]["technologies"]["meca"],
                                    report["player_status"]["technologies"]["gv"]
                                    )

        # parsing colonies
        for colony_status in report["colonies_status"]:
            colony = Colony(self.me,
                            Planet(Star(colony_status["planet"]["star"]["position"]["x"],
                                        colony_status["planet"]["star"]["position"]["y"],
                                        colony_status["planet"]["star"]["position"]["z"]
                                        ),
                                   colony_status["planet"]["numero"]
                                   ),
                            name=colony_status["name"],
                            RO=colony_status["RO"],
                            WF=colony_status["WF"],
                            food=colony_status["food"],
                            parts=colony_status["parts"],
                            food_production=colony_status["food_production"],
                            parts_production=colony_status["parts_production"]
                            )
            self.colonies[colony.name] = colony

        # parsing ships
        for ship_status in report["ships_status"]:
            s = Ship(Player(ship_status["owner_name"]),
                     ship_status["name"],
                     type=ship_status["type"],
                     size=ship_status["size"]
                     )
            s.position = Position(ship_status["position"]["x"],
                                  ship_status["position"]["y"],
                                  ship_status["position"]["z"],
                                  )
            self.ships.append(s)

        # update star.visited
        # visited if we have a colony or if we have a ship
        # store info in brain for persistency
        positions = self.positions_where_i_am()
        for position in positions:
            if Star.exists(position):
                self.brain["visited_stars"].add(position.to_tuple())
        for (x, y, z) in self.brain["visited_stars"]:
            star = Star(x, y, z)
            star.visited = True

        return current_turn

    def positions_where_i_am(self):
        pos_where_i_am = set()
        # positions of my colonies
        colonies_positions = [colony.planet.star.position for colony in self.me.colonies]

        # positions of my ships
        ships_positions = [ship.position for ship in self.me.ships]

        # combnination of ships and colonies positions
        for position in colonies_positions:
            pos_where_i_am.add(position)
        for position in ships_positions:
            pos_where_i_am.add(position)

        return pos_where_i_am

    def play_turn(self, report: dict):
        self.turn = self.parse_report(report)
        self.orders = [f"player {self.name}"]

        # PRODUCTION
        for colony in self.me.colonies:
            self.orders.append(f"PRODUCTION PL {colony.name}")

            available_food = colony.food + colony.food_production
            if available_food > 100 and len(self.me.ships) < 2:
                self.orders.append(f"BUILD 1 BF1 {generate_name()}-{random.randrange(1,99)}")
            else:
                # the half of production to develop WF/RO for production
                WF_trained = int(available_food / 2 // 5)
                food_selling = int(available_food - WF_trained * 5)

                available_parts = int(colony.parts + colony.parts_production)
                RO_manufactured = int(available_parts / 2 // 5)
                parts_selling = int(available_parts - RO_manufactured * 5)

                self.orders.append(f"BUILD {WF_trained} WF")
                self.orders.append(f"SELL {food_selling} food")
                self.orders.append(f"BUILD {RO_manufactured} RO")
                self.orders.append(f"SELL {parts_selling} parts")
                self.orders.append(f"RESEARCH {food_selling} BIO")
                self.orders.append(f"RESEARCH {parts_selling} MECA")

        # MOVEMENTS
        self.orders.append(f"MOVEMENTS")
        for ship in self.me.ships:
            destination = self.closest_unvisited_star(ship)
            x = destination.position.x
            y = destination.position.y
            z = destination.position.z
            self.orders.append(f"JUMP {ship.type}{ship.size} {ship.name} {x} {y} {z}")

        # COMBAT
        self.orders.append(f"COMBAT")

    def closest_unvisited_star(self, ship: Ship):
        # get the list of unvisited stars
        stars = Star.stars.values()
        visited_stars = [Star(x, y, z) for (x, y, z) in self.brain["visited_stars"]]
        unvisited_stars = [star for star in stars if star not in visited_stars]

        # sort the list by distance
        univisted_stars_sorted = sorted(unvisited_stars, key=lambda s: ship.position.distance_to(s.position))

        # remove explo targets already assigned
        valid_sorted_destination = [star for star in univisted_stars_sorted if star not in self.volatile_brain["explo_targets"]]
        # store this target for future explo ships
        destination = valid_sorted_destination[0]
        self.volatile_brain["explo_targets"].append(destination)

        return destination

    def write_order(self):
        with open(f"{self.game_folder}/orders/orders.{self.name}.T{str(self.turn)}.txt", "w") as f:
            f.write('\n'.join(self.orders))      # adding line separators (='\n') between each item of the list


