from bot.names import generate_name
import random

class Bot:
    def __init__(self, config: dict, game_folder: str):
        self.game_folder = game_folder
        self.name = config["name"]

        self.turn = 0
        self.orders = []

    def parse_report(self, report):
        self.report = report
        current_turn = 0
        return current_turn

    def play_turn(self, report):
        self.turn = self.parse_report(report)  # DEBUG : ils sont déjà "parsé"
        self.orders = [f"player {self.name}"]

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

        self.orders.append(f"MOVEMENTS")
        self.orders.append(f"COMBAT")

    def write_order(self):
        with open(f"{self.game_folder}/orders/orders.{self.name}.T{str(self.turn)}.txt", "w") as f:
            f.write('\n'.join(self.orders))      # adding line separators (='\n') between each item of the list


