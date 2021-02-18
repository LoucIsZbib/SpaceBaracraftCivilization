

class Bot:
    def __init__(self, config: dict, game_folder: str):
        self.game_folder = game_folder
        self.name = config["name"]

        self.turn = 0
        self.orders = []

    def parse_report(self, report):
        current_turn = 0
        return current_turn

    def play_turn(self, report):
        self.turn = self.parse_report(report)
        self.orders = []

    def write_order(self):
        with open(f"{self.game_folder}/orders.{self.name}.T{str(self.turn)}.txt", "w") as f:
            f.writelines(self.orders)


