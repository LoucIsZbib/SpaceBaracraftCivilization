"""
IMPORTANT !
do not import anything here, because the following parameters are dirty imported :
from sbc_parameters import *
"""

# naming of thing for comparison
# /!\ should be lowercase !
EU = "eu"           # name of the gobal virtual currency
FOOD = "food"       # name of the BIOLOGICAL currency
PARTS = "parts"     # name of the MECHANICAL currency
WF = "wf"           # WF = working force, works in farms to generate food
RO = "ro"           # RO = robots, works in factory to generate parts

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
COST_WF = 5                         # cost for training 1 WF. Money is food
COST_RO = 5                         # cost for manufacturing 1 RO. Money is part

COST_RESEARCH = 1                   # basic cost for research : 1 EU gives 1 Research_points (+ random)
SELL_TO_GET_EU = 1                  # change ratio when selling food or parts

# ships : name, cost, maintenance, power, cargo, jump_range ...
COST_LEVEL_FIGHTER = 100            # cost for 1 level of Fighter, multiply by level to get ship cost
COST_SCOUT = 100                    # unique cost, scout are mono-level
COST_LEVEL_CARGO = 100              # cost for 1 level of Cargo, multiply by level to get ship cost
BIO_FIGHTER = "bf"
BIO_SCOUT = "bs"
BIO_CARGO = "bc"
MECA_FIGHTER = "mf"
MECA_SCOUT = "ms"
MECA_CARGO = "mc"

def LOG_LEVEL(level: int):
    spacing = "   "
    return level * spacing
