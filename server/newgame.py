import math
import random
import numpy as np
import logging
import os
import yaml
import json

# from typing import List

import server.data as data
from server.names import generate_name
from server.production import food_planet_factor, meca_planet_factor
from server.report import generate_reports, distribute_reports


# STANDARD GAME SETTINGS
STAR_DENSITY_PER_PLAYER = 5     # 6 by player from FarHorizons balance, one is custom-made for each player
GALAXY_DENSITY = 80             # approx from FH = 80 parsec3 / star
MAX_PLANETS_PER_STARS = 7       # as approx seen from FH
MAX_PLANET_SIZE = 5000          # see wiki for planet size and influence on productivity by overpopulation
MIN_PLANET_SIZE = 500           # see wiki for planet size and influence on productivity by overpopulation
BIO_START_TEMP = 25             # start temperature for biological player
BIO_START_HR = 90               # start HR for biological player
MECA_START_TEMP = -50           # start temperature for mecanichal player
MECA_START_HR = 10              # start HR for mechanical player
START_PLANET_SIZE = 3000        # size of initial planet, same for all players
PLAYER_START_POINTS = 20        # number of points to share between BIO and MECA for new player
COLONY_START_POP = 100          # size of population on first colony


# logging
logger = logging.getLogger("sbc")


def newgame(game_name: str, tmp_folder: str, config):
    """ script to create the game objects """
    logger.info("-- Creation of a new game --")

    # Creating folders
    os.makedirs(tmp_folder + "/orders", exist_ok=True)

    # Database selection
    db_name = tmp_folder + '+' + game_name + '.db'
    logger.debug(f"   using {db_name}")
    data.use_db(db_name, testing=True)  # DEBUG
    data.create_tables()

    # init game turn counter
    data.kv["game_turn"] = 0

    # Creates players
    players = create_player(config)

    # Create galaxyplayer.tech.bio
    galaxy_radius = create_galaxy(len(players))
    # print(galaxy_status())

    # Make homes (with new star and custom planets)
    make_homes(players, galaxy_radius)
    # DEBUG
    # for player in players:
    #     print(galaxy_status(player))

    # generate reports for each players
    reports = generate_reports(players)

    # send reports to players
    distribute_reports(reports, tmp_folder, channel="file-yaml")  # DEBUG


def make_homes(players, galaxy_radius):
    """ Creating new star with new planets with custom properties adjusted to player
        Also create a first colony
     """
    logger.info("making homes")
    for player in players:
        # generate new star
        has_been_created = False
        while not has_been_created:
            x, y, z = generate_star(galaxy_radius)
            case, has_been_created = data.Case.get_or_create(x=x, y=y, z=z)
            if case.star:
                logger.debug(f"case {x} {y} {z} has star, reroll")
            else:
                logger.debug(f"case {x} {y} {z} doesn't have a star, creating one for home planet")
                star = data.Star.create(case=case, name=generate_name())

        logger.info(f"   creating new star ({star.name}) and 4 planets for player {player.name}")

        # create custom planets for equal start condition
        """start condition : 4 planets, 1 suitable, 1 almost suitable, 2 not suitable"""
        home_planet_nb, second_planet = random.sample(range(1, 5), 2)
        planets = []
        for i in range(1, 5):
            if i == home_planet_nb:
                humidity, temperature, atmosphere, size = generate_custom_planet(player.tech.bio, player.tech.meca, START_PLANET_SIZE)
            elif i == second_planet:
                humidity, temperature, atmosphere, size = generate_custom_planet(player.tech.meca, player.tech.bio, int(START_PLANET_SIZE * 1.5))
            else:
                humidity, temperature, atmosphere, size = generate_planet(i)
            planets.append({"star": star, "numero": i, "humidity": humidity, "temperature": temperature, "size": size, "atmosphere": atmosphere})
        data.Planet.insert_many(planets).execute()

        # make home colony
        # adjust pop size between bio and meca
        working_force = int(COLONY_START_POP * player.tech.bio / PLAYER_START_POINTS)
        robots = int(COLONY_START_POP * player.tech.meca / PLAYER_START_POINTS)
        planet = data.Planet.get(star=star, numero=home_planet_nb)
        data.Colony.create(planet=planet, owner=player, WF=working_force, RO=robots)

def create_player(config):
    players_name_email = [{"name": player["name"], "email": player["email"]} for player in config["players"]]
    logger.info(f"Creating {len(players_name_email)} Players")
    data.Player.insert_many(players_name_email).execute()
    # useless : if unique constraint is violated, previous instruction raised exception and interrupt the program
    # if len(data.Player.select()) != len(config["players"]):
    #     logger.error(f"number of inserted players ({len(data.Player.select())}) is different from config ({len(config['players'])})")
    #     raise Exception(f"NEWGAME : number of inserted players ({len(data.Player.select())}) is different from config ({len(config['players'])})")
    players = data.Player.select()
    for player in players:
        logger.debug(f"   player {player.name} added")

    # Initialize tech levels
    tech = []
    for player in config["players"]:
        bio = player["bio"]
        meca = player["meca"]
        if bio + meca != PLAYER_START_POINTS:
            raise ValueError(
                f"player BIO and MECA levels are incorrects : BIO({bio}) + MECA({meca}) != start_points({PLAYER_START_POINTS})")
        tech.append({"player": data.Player.get(data.Player.name == player["name"]), "bio": bio, "meca": meca})
    data.Tech.insert_many(tech).execute()

    return players

def create_galaxy(nb_of_player: int,
                  player_density: int = STAR_DENSITY_PER_PLAYER,
                  galaxy_density: int = GALAXY_DENSITY,
                  max_planets_per_star: int = MAX_PLANETS_PER_STARS):
    """
    Create galaxy, stars and planets according to nb_of_player

    Galaxy's form is a sphere
    coords x, y, z starts from 0, there are integers, unity is parsec
    Center of galaxy is shift to keep coords positives

    planets characteristics:
        type : gaz or solid
        humidity : arid (0) to humid (100), think %RH
        temperature : cold (-270) to warm (1000), think °C
        atmosphere : 0.001 to 90 atm (pressure relative to earth)
        size : integer, optimal size of population before serious decreasing due to overpopulation
    These characteristics have influence on life (bio or mechanical):
        corrosion   : more corrosion with more humidity or more warm
        life growth : more growth with humidity or more warm
        Resistance to pressure ?

    Galaxy computation algo :
    nb_of_player --> nb_of_stars --> galaxy_volume --> galaxy_radius

    star creation algo :
    1. pick random coordinates in system : theta[0, 2pi], phi[0, 2pi], radius[0, galaxy_radius]
    2. convert to x y z coordinates with shift (positives coordinates)
    3. assure unicity
    Repeat to get correct number of stars

    planets creation algo:
    For each star :
    1. random nb of planets
    2. define randomly characteristics of each planet
    """
    logger.info("Galaxy creation")

    # number of stars
    nb_of_stars = player_density * nb_of_player

    # computation of galaxy dimensions
    galaxy_volume = galaxy_density * nb_of_stars
    galaxy_radius = math.ceil((galaxy_volume*3/(4*math.pi)) ** (1/3))

    # stars creation
    stars_xyz = set()
    while len(stars_xyz) < nb_of_stars:
        # assure unicity using set
        stars_xyz.add(generate_star(galaxy_radius))
    # store stars
    data.Case.insert_many(stars_xyz).execute()
    cases = data.Case.select()
    logger.info(f"   number of stars created : {len(cases)}")
    with data.db.atomic():
        for case in cases:
            data.Star.create(case=case, name=generate_name())

    # planets creation
    planets = []
    for star in data.Star.select():
        nb_of_planet = random.randrange(0, max_planets_per_star, 1)
        logger.debug(f"{star.name}  x: {star.case.x:>2} y: {star.case.y:>2} x: {star.case.z:>2}")

        for i in range(nb_of_planet):
            humidity, temperature, atmosphere, size = generate_planet(i+1)
            planets.append({"star": star.get_id(), "numero": i+1, "humidity": humidity, "temperature": temperature, "size": size, "atmosphere": atmosphere})
    data.Planet.insert_many(planets).execute()
    logger.info(f"   number of planets created : {len(data.Planet.select())}")

    return galaxy_radius

def generate_star(galaxy_radius: int):
    # spheric coords
    # radius = random.uniform(0, galaxy_radius)
    radius = galaxy_radius * math.sqrt(random.uniform(0, 1))  # appears to be more uniform on circle, less centered
    theta = random.uniform(0, 2 * math.pi)
    phi = random.uniform(0, 2 * math.pi)

    # cartesian integer coords
    x = math.ceil(radius * math.cos(theta) * math.sin(phi)) + galaxy_radius
    y = math.ceil(radius * math.sin(theta) * math.sin(phi)) + galaxy_radius
    z = math.ceil(radius * math.cos(phi)) + galaxy_radius

    return x, y, z

def generate_planet(numero):
    """ Create a random planet """
    # solid = random.choice([True, False])  # for later implementation
    solid = True
    humidity = custom_asymetrical_rnd(0, 50, 100, cohesion=0.5)
    temperature = custom_asymetrical_rnd(-270, 20, 1000, cohesion=3)
    atmosphere = custom_asymetrical_rnd(0, 1, 90, cohesion=3)
    size = random.randrange(MIN_PLANET_SIZE, MAX_PLANET_SIZE, 10)
    logger.debug(f"   planet_nb: {numero}   humidity= {humidity:>6.2f}   temperature={temperature:>7.1f}   size={size:>4}   atmosphere={atmosphere:>7.3f}")

    return humidity, temperature, atmosphere, size

def generate_custom_planet(bio: int, meca: int, planet_size: int = START_PLANET_SIZE):
    """ Create a custom planet to fit player characteristics """
    solid = True
    humidity = MECA_START_HR + bio * (BIO_START_HR - MECA_START_HR) / PLAYER_START_POINTS
    temperature = MECA_START_TEMP + bio * (BIO_START_TEMP - MECA_START_TEMP) / PLAYER_START_POINTS
    atmosphere = custom_asymetrical_rnd(0, 1, 90, cohesion=3)
    size = planet_size
    logger.debug(f"   custom planet :   humidity= {humidity:>6.2f}   temperature={temperature:>7.1f}   size={size:>4}   atmosphere={atmosphere:>7.3f}")

    return humidity, temperature, atmosphere, size

def custom_asymetrical_rnd(left: float, mode: float, right: float, cohesion: float = 2):
    """
    Random pick values within boundary and beta distribution
    we choose alpha=beta in order to have same proba pick on left or on right from mode
    cohesion < 0 : more proba on extremities
    cohesion = 0 : uniform proba
    cohesion > 1 : more proba on center (mode)
    """
    number = np.random.default_rng().beta(cohesion, cohesion)  # alpha = beta = 2 : rather centred on mode , if = 0.5, rather on extrem
    number = (number/0.5*(mode-left) + left) if number < 0.5 else ((number-0.5)/(1-0.5)*(right-mode) + mode)
    return number

def galaxy_status(player: data.Player):
    msg = f"Galaxy viewed from player {player.name}\n"
    stars = data.Star.select()
    msg += f"star number = {len(stars)}" + "\n"
    for star in stars:
        msg += f"{star.name:<10}  x: {star.case.x:>2} y: {star.case.y:>2} x: {star.case.z:>2}  nb_planets={len(star.planets)}" + "\n"
        planets = data.Planet.select().where(data.Planet.star == star)
        for planet in planets:
            msg += f"   planet_nb: {planet.numero}  humidity= {planet.humidity:>6.2f}   temperature={planet.temperature:>7.1f}    atmosphere={planet.atmosphere:>7.3f}    food_factor={food_planet_factor(planet, player):>3.3f}    meca_factor={meca_planet_factor(planet, player):>3.3f}" + "\n"
    return msg