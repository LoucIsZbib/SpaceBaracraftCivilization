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
    """
    Utilise une fabrique pour éviter les doublons

    unique key is player_name: str

    Creation :
        Player( name="GLadOS",
                email="abc@example.com",
                prefered_temperature=40,
                create=True
              )

    Selection :
        Player("GLadOS")
        Player(name="GLadOS")

    """
    players = {}

    def __new__(cls, name: str, email: str = None, prefered_temperature: int = None, create: bool = False):
        """
        unique_key is player_name

        Creation :
            Player( name="GLadOS",
                    email="abc@example.com",
                    prefered_temperature=40,
                    create=True
                  )

        Selection :
            Player("GLadOS")
            Player(name="GLadOS")
        """
        lower_name = name.lower()

        if create:
            # be sure we have the info
            assert isinstance(email, str)
            assert isinstance(prefered_temperature, int)

            # check for unicity
            if cls.exists(lower_name):
                raise LookupError(f"Player({lower_name}) already exists !")

            # this player doesn't exist, creating instance
            instance = object.__new__(cls)

            # store init data
            instance.name = name
            instance.techs = {}       # init technologies by the dedicated method in newgame.py
            instance.email = email
            instance.prefered_temperature = prefered_temperature
            instance.EU = 0
            instance.colonies = []
            instance.ships = []

            # backrefs
            cls.players[lower_name] = instance

            return instance

        else:
            # just retrieve the Player by its name

            if cls.exists(lower_name):
                return cls.players[lower_name]

            else:
                raise LookupError(f"Player({lower_name}) doesn't exists !")

    @classmethod
    def exists(cls, name: str):
        lower_name = name.lower()
        exists = False
        if lower_name in cls.players:
            exists = True
        return exists

class Position:
    """
    Représente les coordonnées d'un secteur (imaginez une case d'un jeu de plateau en 3D)

    Fabrique pour éviter les doublons
    unique key is (x, y, z) <-- tuple

    Only one way to call :
        Position(x, y, z)  # get or create
    """
    positions = {}

    def __new__(cls, x: int, y: int, z: int):
        """
            unique key is (x, y, z) <-- tuple

            Only one way to call :
                Position(x, y, z)  # get or create
        """
        assert isinstance(x, int)
        assert isinstance(y, int)
        assert isinstance(z, int)
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
            # instance.star = None              # usefull ? Star(position) do the job
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
    """
    Fabrique pour éviter les doublons

    unique key is position_object

    Creation :
        Star(position: Position, create=True)

    Selection :
        Star(position_object)
        Star(x, y, z)
        Star(name)
    """
    stars = {}
    star_names = {}

    def __new__(cls, *args, create: bool = False):
        """
        unique key is position_object

        Creation :
            Star(position: Position, create=True)

        Selection :
            Star(position_object)
            Star(x, y, z)
            Star(name)
        """
        if create:
            position = args[0]
            assert isinstance(position, Position)

            # check unicity
            if cls.exists(position):
                raise LookupError(f"Star({position}) exists !")

            # there is no star at this position, create a new one
            instance = object.__new__(cls)

            # store initialisation values
            instance.position = position
            instance._name = None           # has to be choosen by a player
            instance.visited_by = {}        # key = player, value = turn when it has seen
            instance.planets = {}
            instance.seen_by = set()        # list of player_object

            # backrefs
            # position.star = instance  # not usefull, Star(x, y, z) or Star(position) return the star
            cls.stars[position] = instance

            return instance

        else:
            # just retrieve the star object
            if len(args) == 1:
                argument = args[0]
                if isinstance(argument, Position):
                    # selection by position object
                    position = argument
                    return Star.stars[position]

                elif isinstance(argument, str):
                    # selection of a star by its name
                    lower_name = argument.lower()
                    return Star.star_names[lower_name]

                else:
                    # error, this case is not considered
                    raise TypeError(f"Star({argument}) is not a valid star")

            elif len(args) == 3:
                # selection by coords
                x = args[0]
                y = args[1]
                z = args[2]
                position = Position(x, y, z)
                return cls.stars[position]

            else:
                raise TypeError(f"Star() attribute 'position' is needed: Star(position) or Star(x, y, z)")

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
    def update_visited(turn: int):
        # colonies
        for planet, colony in Colony.colonies.items():
            planet.star.visited_by[colony.player] = turn

        # ships
        for (ship_name, player), ship in Ship.ships.items():
            # Is there a star at this position ?
            if Star.exists(ship.position):
                star = Star(ship.position)
                star.visited_by[player] = turn

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
    """
    Fabrique pour éviter les doublons

    unique key is (star, numero)

    creation :
        Planet(star: Star,
               numero: int = 1,
               temperature: int = 30,
               humidity: int = 75,
               create=True
              )

    Selection :
        Planet(star=star_obejct, numero=3)
        Planet(name=planet_name)
    """
    planets = {}

    def __new__(cls, **kwargs):
        """
        unique key is (star, numero)

        creation :
            Planet(star: Star,
                   numero: int = 1,
                   temperature: int = 30,
                   humidity: int = 75,
                   create=True
                  )

        Selection :
            Planet(star=star_obejct, numero=3)
            Planet(name=planet_name)
        """
        name = kwargs.get("name")
        star = kwargs.get("star")
        numero = kwargs.get("numero")
        temperature = kwargs.get("temperature")
        humidity = kwargs.get("humidity")
        create = kwargs.get("create", False)

        if create:
            assert isinstance(star, Star)
            assert isinstance(numero, int)
            assert isinstance(temperature, int)
            assert isinstance(humidity, int)

            index = (star, numero)

            # check for unicity
            if Planet.exists(star, numero):
                raise LookupError(f"Planet({index}) already exists !")

            instance = object.__new__(cls)

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

        elif name:
            # selection by name
            # Star(Earth-3)     /!\ only 1 digit for names -> max 9 planets by system
            full_name = name
            star_name = full_name[:-2]
            numero = int(full_name[-1:])
            star = Star(star_name)
            index = (star, numero)
            if Planet.exists(star, numero):
                return cls.planets[index]
            else:
                raise TypeError(f"Planet({full_name}) is not a valid Planet")

        else:
            # selection by star, numero
            assert isinstance(star, Star)
            assert isinstance(numero, int)
            index = (star, numero)
            return cls.planets[index]

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
        Planet.planets.pop(self.star, self.numero)

    @staticmethod
    def exists(star: Star, numero: int):
        response = False
        if (star, numero) in Planet.planets:
            response = True
        return response

class Colony:
    """
    Fabrique pour éviter les doublons

    unique key is 'planet_object'

    creation :
        Colony( planet=planet_object,
                player=player_object,
                WF=30,
                RO=20,
                create=True
              )

    Selection :
        Colony(planet_object)
        Colony(name)
    """
    colonies = {}

    def __new__(cls, *args, **kwargs):
        """
        unique key is 'planet_object'

        creation :
            Colony( planet=planet_object,
                    player=player_object,
                    WF=30,
                    RO=20,
                    create=True
                  )

        Selection :
            Colony(planet_object)
            Colony(name)
        """
        create = kwargs.get("create", False)
        if create:
            planet = kwargs.get("planet")
            player = kwargs.get("player")
            WF = kwargs.get("WF")
            RO = kwargs.get("RO")
            assert isinstance(planet, Planet)
            assert isinstance(player, Player)
            assert isinstance(WF, int)
            assert isinstance(RO, int)

            # check for unicity
            if planet in cls.colonies:
                # this colony already exists
                raise LookupError(f"Colony on planet {planet} already exists !")

            # the colony doesn't exist, create it
            instance = object.__new__(cls)

            # initialisation
            instance.planet = planet
            instance.player = player
            instance.WF = WF
            instance.RO = RO
            instance.food = 0   # in stockpile
            instance.parts = 0  # in stockpile

            # backref
            player.colonies.append(instance)
            planet.colony = instance
            cls.colonies[planet] = instance

            return instance

        else:
            # just selection
            argument = args[0]

            if isinstance(argument, Planet):
                # selection by planet object
                return cls.colonies[argument]

            elif isinstance(argument, str):
                # selection by name
                # first select the planet of the same name
                planet = Planet(name=argument)
                return cls.colonies[planet]

            else:
                raise LookupError(f"Colony({argument}) selection error ! try planet_object or colony_name")

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
        Colony.colonies.pop(self.planet)

    @property
    def name(self):
        return f"{self.planet.name}"

class Ship:
    """
    Fabrique pour éviter les doublons

    unique key is (ship_name, player)

    Creation :
        Ship( name=ship_name,
              player=player_object,
              size=2,
              type="BF",
              position=position_object,     # mandatory, a ship is always somewhere
              create=True
        )

    Selection :
        Ship (ship_name, player)

    Notes about case-sensitivity:
            - ship.name is case-sensitive
            - Ship selection is case-insentive
            - Ship creation is case-sensitive
            - Ship.ships is lower_case (unique index)
    """
    ships = {}

    def __new__(cls, name: str, player: Player, create=False, size: int = None, ship_type: str = None, position: Position = None):
        """
        unique key is (ship_name, player)

        Creation :
            Ship( name=ship_name,
                  player=player_object,
                  size=2,
                  type="BF",
                  position=position_object,     # mandatory, a ship is always somewhere
                  create=True
            )

        Selection :
            Ship (ship_name, player)
        """
        assert isinstance(name, str)
        assert isinstance(player, Player)
        name_lower = name.lower()
        index = (name_lower, player)

        if create:
            assert isinstance(size, int)
            assert isinstance(ship_type, str)
            assert isinstance(position, Position)

            # check for unicity
            if cls.exists(name, player):
                raise LookupError(f"Ship({name_lower}, {player}) doesn't exists !")

            instance = object.__new__(cls)

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

        else:
            # just selection
            return cls.ships[index]

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

