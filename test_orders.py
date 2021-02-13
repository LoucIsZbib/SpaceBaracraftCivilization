import pytest
from orders import Orders

def test_parsing_line():
    msg = """  \t TRANSFER 1 CU PL "Earth d'en bas" TR 'Firefly de la mort' BAS supercool """
    result = Orders.parsing_line(msg)
    solution = ['transfer', "1", "cu", 'pl', "earth d'en bas", "tr", "firefly de la mort", "bas", "supercool"]
    assert solution == result

