import math
import random
import numpy as np
import logging

import data
from names import generate_name


# STANDARD GAME SETTINGS
STAR_DENSITY_PER_PLAYER = 6     # 6 by player from FarHorizons balance
GALAXY_DENSITY = 80             # approx from FH = 80 parsec3 / star
MAX_PLANETS_PER_STARS = 7       # as approx seen from FH


# logging
logger = logging.getLogger("sbc")


def newgame(game_name: str, tmp_folder: str, config):
    logger.info("-- Creation of a new game --")

    # DEBUG
    data.use_db(tmp_folder + '+' + game_name + '.db', testing=True)
    data.create_tables()

    # DEBUG
    create_galaxy(4)
    # print(galaxy_status())


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
        climat : arid (0) to humid (100), think %RH
        temperature : cold (-270) to warm (1000), think °C
        atmosphere : 0.001 to 90 atm (pressure relative to earth)
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
        # spheric coords
        radius = random.uniform(0, galaxy_radius)
        theta = random.uniform(0, 2*math.pi)
        phi = random.uniform(0, 2*math.pi)

        # cartesian integer coords
        x = math.ceil(radius * math.cos(theta) * math.sin(phi)) + galaxy_radius
        y = math.ceil(radius * math.sin(theta) * math.sin(phi)) + galaxy_radius
        z = math.ceil(radius * math.cos(phi)) + galaxy_radius

        # assure unicity
        stars_xyz.add((x, y, z))
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
            # planet raw characteristics
            # solid = random.choice([True, False])  # for later implementation
            solid = True
            climat = custom_asymetrical_rnd(0, 50, 100, cohesion=0.5)
            temperature = custom_asymetrical_rnd(-270, 20, 1000, cohesion=3)
            atmosphere = custom_asymetrical_rnd(0, 1, 90, cohesion=3)
            logger.debug(f"   planet_nb: {i+1}  climat= {climat:>6.2f}   temperature={temperature:>7.1f}    atmosphere={atmosphere:>7.3f}")

            planets.append({"star": star.get_id(), "numero": i+1, "climat": climat, "temperature": temperature, "atmosphere": atmosphere})
    data.Planet.insert_many(planets).execute()
    logger.info(f"   number of planets created : {len(data.Planet.select())}")


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


def galaxy_status():
    msg = ""
    stars = data.Star.select()
    msg += f"star number = {len(stars)}" + "\n"
    for star in stars:
        msg += f"{star.name:<10}  x: {star.case.x:>2} y: {star.case.y:>2} x: {star.case.z:>2}  nb_planets={len(star.planets)}" + "\n"
        planets = data.Planet.select().where(data.Planet.star == star)
        for planet in planets:
            msg += f"   planet_nb: {planet.numero}  climat= {planet.climat:>6.2f}   temperature={planet.temperature:>7.1f}    atmosphere={planet.atmosphere:>7.3f}" + "\n"
    return msg
