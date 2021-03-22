from bot.names import generate_name
from bot.bot_data import Position, Planet, Player, Colony, Ship, Technologies
import random
from time import time

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

    def parse_report(self, report: dict):
        """ Parse the orders given in dict format and create objects for easy & quick manipulation """
        self.report = report

        # reset the object memory (class attribute)
        Position.reset()
        Planet.reset()
        Player.reset()
        Colony.reset()
        Ship.reset()

        # parsing turn
        current_turn = report["turn"]

        # parsing planets
        for star in report["galaxy_status"]:
            position = Position(star["position"]['x'],
                                star['position']['y'],
                                star['position']['z'])
            for planet in star['planets']:
                p = Planet(position, planet['numero'],
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

        # # parsing players
        self.me = Player(self.name)
        self.me.EU = report["player_status"]["EU"]
        self.me.tech = Technologies(report["player_status"]["technologies"]["bio"],
                                    report["player_status"]["technologies"]["meca"],
                                    report["player_status"]["technologies"]["gv"]
                                    )

        # parsing colonies
        for colony_status in report["colonies_status"]:
            colony = Colony(self.me,
                            Planet(Position(colony_status["planet"]["star"]["position"]["x"],
                                            colony_status["planet"]["star"]["position"]["y"],
                                            colony_status["planet"]["star"]["position"]["z"]),
                                   colony_status["planet"]["numero"]
                                   ),
                            name=colony_status["colony_name"],
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

        return current_turn

    def play_turn(self, report: dict):
        self.turn = self.parse_report(report)
        self.orders = [f"player {self.name}"]

        # PRODUCTION
        for colony in self.report["colonies_status"]:
            self.orders.append(f"PRODUCTION PL {colony['colony_name']}")

            available_food = int(colony["food"] + colony["food_production"])
            if available_food > 100:
                self.orders.append(f"BUILD 1 BF1 {generate_name()}-{random.randrange(1,99)}")
            else:
                WF_trained = int(available_food / 2 // 5)
                food_selling = int(available_food - WF_trained * 5)

                available_parts = int(colony["parts"] + colony["parts_production"])
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

        # COMBAT
        self.orders.append(f"COMBAT")

    def write_order(self):
        with open(f"{self.game_folder}/orders/orders.{self.name}.T{str(self.turn)}.txt", "w") as f:
            f.write('\n'.join(self.orders))      # adding line separators (='\n') between each item of the list


