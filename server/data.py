import peewee as p
from playhouse.kv import KeyValue
from typing import List
import math
import json

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
            # instance.players = {}      # Not necessary, info present within class
            # instance.positions = {}
            # instance.stars = {}
            # instance.planets = {}
            # instance.colonies = {}
            # instance.ships = {}

            cls._instance = instance
            return instance

    def load_gamedata(self, filename):
        """ Loads game data from JSON file """
        # loads data from file
        with open(filename, "r", encoding='utf8') as f:
            data = json.load(f)

        # place the data to the good place
        # TODO : to be done

    def dump_gamedata(self, filename):
        """ dumps game data to a json file """
        # create a unique structure with all data
        data = {}
        # TODO : implement this

        # save data to json file
        with open(filename, "w", encoding="utf8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

@dataclass
class Technologies:
    level: int
    progression: int

class Player:
    """ Fabrique pour éviter les doublons """
    players = {}

    def __new__(cls, *args, **kwargs):
        """
        unique_key is player_name

        Possible :
            Player("GLadOS")
            Player(name="GLadOS")
            Player("GLadOS", email="abc@example.com", prefered_temperature=40)
            Player(name="GLadOS", email="abc@example.com", prefered_temperature=40)
        """
        if args:
            name = args[0]
        elif kwargs:
            name = kwargs["name"]
        else:
            raise TypeError("Player() attribute 'name' needed : Player('Bob') or Player(name='Bob')")

        lower_name = name.lower()

        # check for unicity
        if lower_name in cls.players:
            return cls.players[lower_name]
        else:
            # this player doesn't exist, creating instance
            instance = object.__new__(cls)

            # retrieve initialisation data
            email = kwargs.get("email")
            prefered_temperature = kwargs.get("prefered_temperature")
            assert email
            assert prefered_temperature

            # store init data
            instance.name = name
            instance.techs = {}       # init technologies by the dedicated method in newgame.py
            instance.email = email
            instance.prefered_temperature = prefered_temperature
            instance.EU = 0
            instance.colonies = []
            instance.ships = []

            cls.players[lower_name] = instance
            return instance

class Position:
    """ Fabrique pour éviter les doublons """
    positions = {}

    def __new__(cls, x: int, y: int, z: int):
        """
            unique key is (x, y, z) <-- tuple

            Only one way to call :
                Position(x, y, z)
        """
        coords = (x, y, z)
        if coords in cls.positions:
            # this position already exists, return it
            return cls.positions[coords]

        else:
            # this position doesn't exist, create it
            instance = object.__new__(cls)

            # initialisation
            instance.x = x
            instance.y = y
            instance.z = z
            instance.distances = {}

            # for backrefs
            instance.ships = set()
            # instance.star = None  # usefull ?

            cls.positions[coords] = instance
            return instance

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

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
        }

class Star:
    """ Fabrique pour éviter les doublons """
    stars = {}
    star_names = {}

    def __new__(cls, *args, **kwargs):
        """
            unique key is position_object

            Possible call :
                Star(position_object)
                Star(x, y, z)
                Star(name)              # for selection only

        """
        # invocation parsing
        if len(args) == 1:
            argument = args[0]
            if isinstance(argument, Position):
                position = argument
            elif isinstance(argument, str):
                # selection of a star by its name : selection only
                name = argument.lower()
                return Star.star_names[name]
            else:
                # error, this case is not considered
                raise TypeError(f"Star({argument}) is not a valid star")
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
            instance._name = None                # has to be choose by a player
            instance.visited_by = set()         # list of player_object
            instance.planets = {}

            # backrefs
            # position.star = instance  # not usefull, Star(x, y, z) or Star(position) return the star

            cls.stars[position] = instance
            return instance

    def to_dict(self):
        return {
            "name": self.name,
            "position": self.position.to_dict()
        }

    @staticmethod
    def exists(position: Position):
        response = False
        if position in Star.stars:
            response = True
        return response

    @staticmethod
    def update_visited():
        # colonies
        for planet, colony in Colony.colonies.items():
            planet.star.visited_by.add(colony.player)

        # ships
        for (ship_name, player), ship in Ship.ships.items():
            # Is there a star at this position ?
            if Star.exists(ship.position):
                star = Star(ship.position)
                star.visited_by.add(player)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        if self._name:
            raise AttributeError(f"The star ({self._name} already has a name, can't assign a new one")
        else:
            self._name = value
            Star.star_names[value.lower()] = self

class Planet:
    """ Fabrique pour éviter les doublons """
    planets = {}

    def __new__(cls, *args, **kwargs):
        """
        unique key is (star, numero)

        Possible
            Planet(star: Star, numero: int)
            Planet(star=star_object,
                   numero=1,
                   temperature=30,
                   humidity=75,
                  )
            Planet(name : str)                # for selection only
        """
        if len(args) == 1:
            # selection by name : only selection
            # Star(Earth-3)     /!\ only 1 digit for names -> max 9 planets by system
            full_name = args[0]
            star_name = full_name[:-2]
            numero = full_name[-1:]
            star = Star(star_name)
            if Planet.exists(star, numero):
                return cls.planets[star, numero]
            else:
                raise TypeError(f"Planet({full_name}) is not a valid Planet")

        elif len(args) >= 2:
            star = args[0]
            numero = args[1]
        elif kwargs:
            star = kwargs['star']
            numero = kwargs["numero"]
        else:
            raise Exception(f"Planet call has no args, kwargs")
        index = (star, numero)

        if index in cls.planets:
            # this planet exists, return it
            return cls.planets[index]

        else:
            # this planet doesn't exists, create it
            instance = object.__new__(cls)

            # initialisation
            temperature = kwargs.get("temperature")
            humidity = kwargs.get("humidity")
            assert temperature
            assert humidity

            # store data
            instance.star = star
            instance.numero = numero
            instance.temperature = temperature
            instance.humidity = humidity
            instance.colony = None

            # backref
            star.planets[numero] = instance

            cls.planets[index] = instance
            return instance

    def to_dict(self):
        return {
            "star": self.star.to_dict(),
            "numero": self.numero,
            "temperature": self.temperature,
            'humidity': self.humidity
        }

    def localisation_to_dict(self):
        return {
            "star": self.star.to_dict(),
            "numero": self.numero
        }

    @property
    def name(self):
        return f"{self.star.name}-{self.numero}"

    def delete(self):
        # remove backrefs
        self.star.planets.pop(self.numero)

    @staticmethod
    def exists(star: Star, numero: int):
        response = False
        if (star, numero) in Planet.planets:
            response = True
        return response

class Colony:
    """ Fabrique pour éviter les doublons """
    colonies = {}

    def __new__(cls, *args, **kwargs):
        """
            unique key is 'planet_object'

            Possible
                Colony(planet_object)           # only to get, not to create
                Colony( planet=planet_object,
                        player=player_object,
                        WF=30,
                        RO=20
                      )
                Colony(name)                    # for selection only, not to create
        """
        if len(args) ==1:
            if isinstance(args[0], Planet):
                planet = args[0]
            elif isinstance(args[0], str):
                planet = Planet(args[0])
            else:
                raise TypeError(f"Colony({args}) doesn't exist")
        elif kwargs:
            planet = kwargs["planet"]
        else:
            raise Exception(f"Colony call with bad or without *args({args}) or **kwargs({kwargs})")

        if planet in cls.colonies:
            # this colony already exists
            return cls.colonies[planet]

        else:
            # the colony doesn't exist, create it
            instance = object.__new__(cls)

            # data for initialisation
            player = kwargs.get("player")
            WF = kwargs.get("WF")
            RO = kwargs.get("RO")
            assert player
            assert WF
            assert RO

            # initialisation
            instance.planet = planet
            instance.player = player
            instance.WF = WF
            instance.RO = RO
            instance.food = 0               # in stockpile
            instance.parts = 0              # in stockpile

            # backref
            player.colonies.append(instance)
            planet.colony = instance

            cls.colonies[planet] = instance
            return instance

    def to_dict(self):
        return {
            "name": self.name,
            "WF": self.WF,
            "RO": self.RO,
            "food": self.food,
            "parts": self.parts
        }

    def delete(self):
        # remove backrefs
        self.player.colonies.remove(self)
        self.planet.colony = None

    @property
    def name(self):
        return f"{self.planet.name}"

class Ship:
    """ Fabrique pour éviter les doublons """
    ships = {}

    def __new__(cls, *args, **kwargs):
        """
            unique key is (ship_name, player)

            Possible
                Ship(ship_name, player_object)
                Ship( name=ship_name,
                      player=player_object,
                      size=2,
                      type="BF",
                      position=position_object  # mandatory, a ship is always somewhere
                    )

            Notes about case-sensitivity:
            - ship.name is case-sensitive
            - Ship selection is case-insentive
            - Ship creation is case-sensitive
            - Ship.ships is case-insensitive
        """
        if len(args) ==2:
            name = args[0]
            player = args[1]
        elif kwargs:
            name = kwargs["name"]
            player = kwargs["player"]
        else:
            raise TypeError(f"Ship with no *args or **kwargs")
        name_lower = name.lower()
        index = (name_lower, player)

        if index in cls.ships:
            # the ship already exists, return it
            return cls.ships[index]

        else:
            # this ship doesn't exist, create it
            instance = object.__new__(cls)

            # initialisation
            ship_type = kwargs.get("type")
            size = kwargs.get("size")
            position = kwargs.get("position")
            assert ship_type
            assert size
            assert position
            assert isinstance(position, Position)

            # storing init values
            instance.name = name
            instance.player = player
            instance.type = ship_type
            instance.size = size
            instance._position = None
            instance.position = position

            # backrefs
            # position backref is handled by property because it can change during game
            player.ships.append(instance)

            cls.ships[index] = instance
            return instance

    def to_dict(self):
        return {
            "owner_name": self.player.name,
            "type": self.type,
            "name": self.name,
            "size": self.size,
            "position": self.position.to_dict(),
        }

    @staticmethod
    def parse_ship(arguments: List[str]):
        full_type = arguments[0]
        ship_size = int(full_type[2:])
        ship_type = full_type[:2].lower()
        ship_name = arguments[1]
        return ship_type, ship_size, ship_name

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value: Position):
        assert isinstance(value, Position)
        self._position = value
        # creating backref to easily get all ships on a position
        value.ships.add(self)

    def delete(self):
        # removing backref
        self._position.ships.remove(self)
        self.player.ships.remove(self)
        index = (self.name.lower(), self.player)
        del self.ships[index]

    @staticmethod
    def exists(ship_name: str, player: Player):
        response = False
        index = (ship_name.lower(), player)
        if index in Ship.ships:
            response = True
        return response

