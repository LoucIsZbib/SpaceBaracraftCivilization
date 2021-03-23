import peewee as p
from playhouse.kv import KeyValue
from typing import List
import math

from server.names import generate_name


from dataclasses import dataclass

class GameData:
    """
    Global container for game memory
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        """ Singleton """
        if cls._instance:
            return cls._instance
        else:
            instance = object.__new__(cls)

            # initialisation
            instance.turn = 0
            instance.players = {}
            instance.positions = {}
            instance.stars = {}
            instance.planets = {}
            instance.colonies = {}
            instance.ships = {}

            cls._instance = instance
            return instance

@dataclass
class Technologies:
    bio: int
    meca: int
    gv: int

class Player:
    """ Fabrique pour éviter les doublons """
    players = {}

    def __new__(cls, *args, **kwargs):
        """
        Possible :
            Player("GLadOS")
            Player(name="GLadOS", email="abc@example.com", prefered_temperature=40)
        """
        if args:
            name = args[0]
        elif kwargs:
            name = kwargs["name"]
            email = kwargs["email"]
            prefered_temperature = kwargs["prefered_temperature"]
        else:
            raise Exception("Error Player_object creation: no *args, no **kwargs")

        # check for unicity
        if name in cls.players:
            return cls.players[name]
        else:
            # this player doesn't exist, creating instance
            instance = object.__new__(cls)

            # initialisation
            if "email" not in locals() or "prefered_temperature" not in locals():
                raise Exception("Player creation : email, prefered_temperature needed !")
            instance.techs = Technologies(bio=10, meca=10, gv=5)        # TODO : gérer l'initialisation des techs selon les choix du joueur ?
            instance.email = email
            instance.prefered_temperature = prefered_temperature
            instance.EU = 0

            cls.players[name] = instance
            return instance







class Case(p.Model):
    x = p.IntegerField()
    y = p.IntegerField()
    z = p.IntegerField()

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z

        }

    @staticmethod
    def distance(a, b):
        return math.sqrt(  (a.x - b.x) ** 2
                         + (a.y - b.y) ** 2
                         + (a.z - b.z) ** 2
                         )

    class Meta:
        database = db  # This model uses the 'game.db' database
        indexes = (
            (("x", "y", "z"), True),  # unique index sur x, y , z
        )

class Star(p.Model):
    case = p.ForeignKeyField(Case, backref='star')
    name = p.CharField()

    def to_dict(self):
        return {"name": self.name,
                "position": self.case.to_dict(),
                }

    class Meta:
        database = db  # This model uses the 'game.db' database
        constraints = [p.SQL('UNIQUE ("name" COLLATE NOCASE)')]

class Planet(p.Model):
    star = p.ForeignKeyField(Star, backref='planets')
    numero = p.IntegerField()
    humidity = p.FloatField()
    temperature = p.FloatField()
    size = p.IntegerField()
    atmosphere = p.FloatField()

    def to_dict(self):
        return {
            "numero": self.numero,
            "humidity": self.humidity,
            "temperature": self.temperature,
        }

    def localisation_to_dict(self):
        return {
            "star": self.star.to_dict(),
            "numero": self.numero
        }

    class Meta:
        database = db  # This model uses the 'game.db' database
        indexes = (
            (("star", "numero"), True),  # unique index sur star and numero
        )

class PlanetNames(p.Model):
    """ Each planet could be nammed differently by each player """
    player = p.ForeignKeyField(Player, backref="planets_names")
    planet = p.ForeignKeyField(Planet, backref="names")

    class Meta:
        database = db  # This model uses the 'game.db' database
        indexes = (
            (("player", "planet"), True),  # unique index sur star and numero
        )

class StarVisited(p.Model):
    star = p.ForeignKeyField(Star, backref="visited")
    player = p.ForeignKeyField(Player, backref="star_visited")

    class Meta:
        database = db  # This model uses the 'game.db' database
        indexes = (
            (("player", "star"), True),  # unique index sur star and numero
        )

class Colony(p.Model):
    planet = p.ForeignKeyField(Planet, backref="colony")
    player = p.ForeignKeyField(Player, backref="colonies")
    name = p.CharField()
    WF = p.IntegerField(default=0)
    RO = p.IntegerField(default=0)
    food = p.IntegerField(default=0)
    parts = p.IntegerField(default=0)

    def to_dict(self):
        return {
            "colony_name": self.name,
            "WF": self.WF,
            "RO": self.RO,
            "food": self.food,
            "parts": self.parts
        }

    class Meta:
        database = db  # This model uses the 'game.db' database
        indexes = (
            (("planet", "player"), True),  # unique index sur star and numero
        )
        constraints = [p.SQL('UNIQUE ("name" COLLATE NOCASE)')]

class Ship(p.Model):
    player = p.ForeignKeyField(Player, backref="ships")
    case = p.ForeignKeyField(Case, backref="ships")
    type = p.CharField()
    name = p.CharField()
    size = p.IntegerField()

    def to_dict(self):
        return {
            "owner_name": self.player.name,
            "type": self.type,
            "name": self.name,
            "size": self.size,
            "position": self.case.to_dict(),
        }

    @staticmethod
    def parse_ship(arguments: List[str]):
        full_type = arguments[0]
        ship_size = int(full_type[2:])
        ship_type = full_type[:2]
        ship_name = arguments[1]
        return ship_type, ship_size, ship_name

    class Meta:
        database = db  # This model uses the 'game.db' database
        indexes = (
            (("name", "player"), True),  # unique index sur name and player
        )
        constraints = [p.SQL('UNIQUE ("name" COLLATE NOCASE)')]

