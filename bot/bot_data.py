from dataclasses import dataclass
"""
Contrairement au moteur de jeu, le stockage n'est pas via une bdd
"""

class Position:
    """
    Fabrique :
    Si une case avec les coords (x, y, z) existe déjà, renvoie cette case
    Sinon en crée une nouvelle et l'enregistre
    """
    positions = {}

    def __new__(cls, x: int, y: int, z: int):
        """ x, y, z are like the unique index of an SQL table, other parameters have to be added later """
        coords = (x, y, z)
        if coords in cls.positions:
            # a case at theses coords already exists
            return cls.positions[coords]
        else:
            # no case exists, need to be created first
            instance = object.__new__(cls)
            cls.positions[coords] = instance
            instance.x = x
            instance.y = y
            instance.z = z
            instance.ships = set()
            return instance

    @classmethod
    def reset(cls):
        cls.positions = {}


class Planet:
    """ Fabrique pour éviter les doublons """
    planets = {}

    def __new__(cls, position: Position, numero: int, **kwargs):
        """ position & numero are like the unique index of an SQL table, other parameters have to be added later """
        unique_index = (position, numero)
        if unique_index in cls.planets:
            # The planet exists, return it
            return cls.planets[unique_index]
        else:
            # it doesn't exist, create the planet
            instance = object.__new__(cls)
            cls.planets[unique_index] = instance
            instance.position = position
            instance.numero = numero
            instance.temperature = kwargs.get('temperature')
            instance.humidity = kwargs.get('humidity')
            instance.food_factor = kwargs.get("food_factor")
            instance.meca_factor = kwargs.get("meca_factor")
            instance.max_food_prod = kwargs.get("max_food_prod")
            instance.max_parts_prod = kwargs.get('max_parts_prod')
            instance.max_ro = kwargs.get("max_ro")
            instance.max_wf = kwargs.get("max_wf")
            return instance

    @classmethod
    def reset(cls):
        cls.planets = {}

class Player:
    """ Fabrique pour éviter les doublons """
    players = {}

    def __new__(cls, name: str):
        """ name is like the unique index of an SQL table, other parameters have to be added later """
        if name in cls.players:
            # The planet exists, return it
            return cls.players[name]
        else:
            # it doesn't exist, create the planet
            instance = object.__new__(cls)
            cls.players[name] = instance
            instance.name = name
            instance.ships = set()  # to easily get all ships from a player
            instance.colonies = []

            return instance

    @classmethod
    def reset(cls):
        cls.players = {}

@dataclass
class Technologies:
    bio: int
    meca: int
    gv: int

class Colony:
    """ Fabrique pour éviter les doublons """
    colonies = {}

    def __new__(cls, player: Player, planet: Planet, **kwargs):
        """ player, planet are like the unique index of an SQL table, other parameters have to be added later """
        unique_index = (player, planet)
        if unique_index in cls.colonies:
            # The planet exists, return it
            return cls.colonies[unique_index]
        else:
            # it doesn't exist, create the planet
            instance = object.__new__(cls)
            cls.colonies[unique_index] = instance
            instance.player = player
            instance.planet = planet
            instance.name = kwargs.get("name")
            instance.RO = kwargs.get("RO")
            instance.WF = kwargs.get("WF")
            instance.food = kwargs.get("food")
            instance.parts = kwargs.get("parts")
            instance.food_production = kwargs.get("food_production")
            instance.parts_production = kwargs.get("parts_production")

            # assure backrefs
            player.colonies.append(instance)

            return instance

    @classmethod
    def reset(cls):
        cls.colonies = {}


class Ship:
    """ Fabrique pour éviter les doublons """
    ships = {}

    def __new__(cls, player: Player, ship_name: str, **kwargs):
        """ player, ship_name are like the unique index of an SQL table, other parameters have to be added later """
        unique_index = (player, ship_name)
        if unique_index in cls.ships:
            # The planet exists, return it
            return cls.ships[unique_index]
        else:
            # it doesn't exist, create the planet
            instance = object.__new__(cls)
            cls.ships[unique_index] = instance
            instance.player = player
            instance.name = ship_name
            instance.type = kwargs.get("type")
            instance.size = kwargs.get("size")
            instance._position = None

            # creating backref to easily get all ships from a player
            player.ships.add(instance)

            return instance

    @classmethod
    def reset(cls):
        cls.ships = {}

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value: Position):
        if value:
            self._position = value
            # creating backref to easily get all ships on a position
            value.ships.add(self)
