from server.data import Player, Technologies

import random

import logging

# logging
logger = logging.getLogger("sbc")


def upgrade_tech(player: Player, tech_str: str, qty: int):
    """
    The cost for upgrading 1 level of a tech, is the current_level² in EU
    real qty invested in research is qty multiplied by a random factor (25% of invested amount)
    this real_investement is reversed to a "progression bar"
    When the progression bar reach the cost for upgrading, the level is gained
    surplus is versed to progression bar for next level

    returns new_level, level_gain
    """
    tech = player.techs[tech_str]
    initial_level = tech.level

    random_factor = random.uniform(0.75, 1.25)
    real_investment = int(qty * random_factor)

    tech.progression += real_investment

    # current_level² = cost_for_next_level
    while tech.progression >= tech.level ** 2:
        # level up
        tech.progression -= tech.level ** 2
        tech.level += 1

    return tech.level, tech.level - initial_level
