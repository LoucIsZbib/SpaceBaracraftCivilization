"""
IMPORTANT !
do not import anything here, because the following parameters are dirty imported :
from sbc_parameters import *
"""

EU = "eu"           # name of the gobal virtual currency
FOOD = "food"       # name of the BIOLOGICAL currency
PARTS = "parts"     # name of the MECHANICAL currency

# === STANDARD GAME SETTINGS ===
# Galaxy creation
STAR_DENSITY_PER_PLAYER = 5         # 6 by player from FarHorizons balance, one is custom-made for each player
GALAXY_DENSITY = 80                 # approx from FH = 80 parsec3 / star
MAX_PLANETS_PER_STARS = 7           # as approx seen from FH
MAX_PLANET_SIZE = 5000              # see wiki for planet size and influence on productivity by overpopulation
MIN_PLANET_SIZE = 500               # see wiki for planet size and influence on productivity by overpopulation

# Start conditions
START_PLANET_SIZE = 3000            # size of initial planet, same for all players
PLAYER_START_POINTS = 20            # number of points to share between BIO and MECA for new player
COLONY_START_POP = 100              # size of population on first colony

# Biome characteristics
BIO_START_TEMP = 25                 # start temperature for biological player           -- initial 25
BIO_START_HR = 50                   # start HR for biological player                    -- initial 90
MECA_START_TEMP = 25                # start temperature for mecanichal player           -- initial -50
MECA_START_HR = 50                  # start HR for mechanical player                    -- initial 10
OPTIMAL_TEMP_BIOLOGICAL = 25        # optimal temperature in °C for biological species  -- initial 25
OPTIMAL_RH_BIOLOGICAL = 50          # optimal Humidity in % RH for biological species   -- initial 100
OPTIMAL_TEMP_MECA = 25              # optimal temperature in °C for mechanical species  -- initial -50
OPTIMAL_RH_MECA = 50                # optimal Humidity in % RH for mechanical species   -- initial 0

# Adaptation characteristics
BASE_STD_TEMP = 20                  # base standard deviation for temperature adaptation (gaussian law, std)
BASE_STD_RH = 10                    # base standard deviation for Humidity adaptation (gaussian law, std)

# Economic characteristics
POP_THRESHOLD = 2000                # Factor of max pop size in a colony
BASE_MAINTENANCE_WF = 1             # base cost of maintenance for 1 WF
BASE_MAINTENANCE_RO = 3             # base cost of maintenance for 1 WF or 1 RO
BASE_PRODUCTIVITY = 2               # base food/spare-parts generation per WF or RO


def LOG_LEVEL(level: int):
    spacing = "   "
    return level * spacing
