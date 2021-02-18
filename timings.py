from time import time
from server.orders import Orders


# orders parsing from file
file = "orders.EXAMPLE.txt"
start = time()
res = Orders.parsing_file(file)
stop = time()
print(f"{(stop-start)*1000:.3f} ms -- {res}")

