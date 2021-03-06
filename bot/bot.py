

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
            self.orders.append(f"SELL {colony['food']} food")
            self.orders.append(f"SELL {colony['parts']} meca")
            self.orders.append("RESEARCH 100 BIO")

        self.orders.append(f"MOVEMENTS")
        self.orders.append(f"COMBAT")

    def write_order(self):
        with open(f"{self.game_folder}/orders/orders.{self.name}.T{str(self.turn)}.txt", "w") as f:
            f.write('\n'.join(self.orders))      # adding line separators (='\n') between each item of the list


