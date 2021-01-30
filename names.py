import random
import string

VOWELS = ["a", "e", "i", "o", "u", "y", "ou", "au", "eu", "ei", "ai", "ay", "ey", "ua"]
# CONSONANTS = ", ".join(set(string.ascii_lowercase) - set(VOWELS))
FIRST = ["a", "b", "c", "d", "f", "g", "h", "j", "k", "l", "m", "n", "p", "q", "r", "s", "t", "v", "w", "x", "z", "th", "bh", "dh", "ph"]
CONSONANTS = ["b", "c", "d", "f", "g", "h", "j", "k", "l", "m", "n", "p", "q", "r", "s", "t", "v", "w", "x", "z", "th", "bh", "dh", "rr", "ph", "ngu", "ng", "ll", "ss", "rm", "nt", "pp"]

def generate_name():
    length = random.randrange(3, 6)

    word = ""
    for i in range(length):
        if i == 0:
            word += random.choice(FIRST)
        elif i % 2 == 0:
            word += random.choice(CONSONANTS)
        else:
            word += random.choice(VOWELS)
    return word


if __name__ == "__main__":
    for i in range(30):
        print(generate_name())

