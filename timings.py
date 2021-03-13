from time import time
from timeit import timeit

def forin(ship: str):
    if "TR" in ship:
        return True
    else:
        return False

def start(ship: str):
    if ship.startswith("TR"):
        return True
    else:
        return False


# Python 3.9 only
# def removepr(ship: str):
#     return int(ship.removeprefix("TR"))

def replac(ship: str):
    return int(ship.replace("TR", ""))

def lsp(ship: str):
    return int(ship.lstrip('TR'))

def crochet(ship: str):
    return int(ship[2:])


# t = timeit("removepr('TR20')", number=1000, globals=globals())
# print(f"'removeprefix' timeit = {t:.5f} ms")

t = timeit("replac('TR20')", number=1000, globals=globals())
print(f"'x.replace' timeit = {t:.5f} ms")

t = timeit("crochet('TR20')", number=1000, globals=globals())
print(f"'ship[2:]' timeit = {t:.5f} ms")

t = timeit("lsp('TR20')", number=1000, globals=globals())
print(f"'x.lstrip' timeit = {t:.5f} ms")


