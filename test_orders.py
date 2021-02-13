import pytest
from orders import Orders

def test_parsing_line():
    msg = """  \t TRANSFER 1 CU PL "Earth d'en bas" TR 'Firefly de la mort' BAS supercool """
    result = Orders.parsing_line(msg)
    solution = ['transfer', "1", "cu", 'pl', "earth d'en bas", "tr", "firefly de la mort", "bas", "supercool"]
    assert solution == result

def test_parsing_file():
    content = '''# This is a command, works also within a line : everything on right is ignored
# First line = name of the Player
player Flibustiers

# First part = PRODUCTION
PRODUCTION PL Earth
build 50 WF

Production PL "Red Mars"
REsearch 10 bio




# Second part = MOVEMENTS
MOVEMENTS
jump FF firefly PL Venus

Orbit DD "ISS barakuda" PL Earth

# Last part = COMBAT
COMBAT
attack FF Firefly PL Venus

'''
    filename = "temporary_file"
    with open(filename, "w") as f:
        f.write(content)

    player, production, movements, combat = Orders.parsing_file(filename)

    assert player == ["flibustiers"]
    assert production == [["pl", "earth"], ["build", "50", "wf"], ["pl", "red mars"], ['research', '10', 'bio']]
    assert movements == [["jump", "ff", "firefly", "pl", "venus"], ["orbit", "dd", "iss barakuda", "pl" , "earth"]]
    assert combat == [["attack", "ff", "firefly", "pl", "venus"]]

