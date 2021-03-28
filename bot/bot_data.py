from dataclasses import dataclass
import math
"""
Contrairement au moteur de jeu, le stockage n'est pas via une bdd
"""

class Position:
    """
    Fabrique :
    Si une position avec les coords (x, y, z) existe déjà, renvoie cette position
    Sinon en crée une nouvelle et l'enregistre
    """
    positions = {}

    def __new__(cls, x: int, y: int, z: int):
        """ x, y, z are like the unique index of an SQL table, other parameters have to be added later """
        coords = (x, y, z)
        if coords in cls.positions:
            # a position at theses coords already exists
            return cls.positions[coords]
        else:
            # no position exists, need to be created first
            instance = object.__new__(cls)
            cls.positions[coords] = instance
            instance.x = x
            instance.y = y
            instance.z = z
            instance.ships = set()
            instance.distances = {}

            return instance

    @classmethod
    def reset(cls):
        cls.positions = {}

    def to_tuple(self):
        return self.x, self.y, self.z

    def distance_to(self, position):
        """ compute the distance from this postion (self) to another Position
            Cache previously calculated distances
        """
        coords = (position.x, position.y, position.z)

        # check if this has already been calculated
        if coords in self.distances:
            distance = self.distances[coords]

        else:
            distance = math.sqrt((self.x - position.x) ** 2
                                 + (self.y - position.y) ** 2
                                 + (self.z - position.z) ** 2
                                 )
            self.distances[coords] = distance

        return distance

class Star:
    """ Fabrique pour éviter les doublons """
    stars = {}

    def __new__(cls, *args, **kwargs):
        """
            unique key is position_object

            Possible call :
                Star(position_object)
                Star(x, y, z)

        """
        if len(args) == 1:
            position = args[0]
            assert isinstance(position, Position)
        elif len(args) == 3:
            x = args[0]
            y = args[1]
            z = args[2]
            position = Position(x, y, z)
        else:
            raise TypeError(f"Star() attribute 'position' is needed: Star(position) or Star(x, y, z)")

        if position in cls.stars:
            # this star already exists, return it
            return cls.stars[position]

        else:
            # there is no star at this position, create a new one
            instance = object.__new__(cls)

            # store initialisation values
            instance.position = position
            instance.name = None                # has to be choose by a player
            instance.visited = False         # list of player_object
            instance.planets = {}

            # backrefs
            # position.star = instance  # not usefull, Star(x, y, z) or Star(position) return the star

            cls.stars[position] = instance
            return instance

    @classmethod
    def reset(cls):
        cls.stars = {}

    @staticmethod
    def exists(position: Position):
        response = False
        if position in Star.stars:
            response = True
        return response

class Planet:
    """ Fabrique pour éviter les doublons """
    planets = {}

    def __new__(cls, star: Star, numero: int, **kwargs):
        """ star & numero are like the unique index of an SQL table, other parameters have to be added later """
        unique_index = (star, numero)
        if unique_index in cls.planets:
            # The planet exists, return it
            return cls.planets[unique_index]
        else:
            # it doesn't exist, create the planet
            instance = object.__new__(cls)
            cls.planets[unique_index] = instance
            instance.star = star
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
