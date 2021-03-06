import peewee as p
from playhouse.kv import KeyValue

from server.names import generate_name

db = p.SqliteDatabase(None, autoconnect=True)

kv = None

def use_db(path_to_db: str = "game", testing: bool = False):
    global kv
    if testing:
        db.init(':memory:')
    else:
        db.init(f"{path_to_db}")

    kv = KeyValue(database=db, table_name="keyvalue")

class Player(p.Model):
    name = p.CharField()
    email = p.CharField()
    EU = p.IntegerField(default=0)

    @property
    def bio(self):
        return self.techs.where(Tech.tech == "bio").get().level

    @property
    def meca(self):
        return self.techs.where(Tech.tech == "meca").get().level

    class Meta:
        database = db  # This model uses the 'game.db' database
        constraints = [p.SQL('UNIQUE ("name" COLLATE NOCASE)')]

class Tech(p.Model):
    player = p.ForeignKeyField(Player, backref="techs")
    tech = p.CharField()
    level = p.IntegerField()
    progression = p.IntegerField(default=0)

    class Meta:
        database = db  # This model uses the 'game.db' database

class Case(p.Model):
    x = p.IntegerField()
    y = p.IntegerField()
    z = p.IntegerField()

    class Meta:
        database = db  # This model uses the 'game.db' database
        indexes = (
            (("x", "y", "z"), True),  # unique index sur x, y , z
        )

class Star(p.Model):
    case = p.ForeignKeyField(Case, backref='star')
    name = p.CharField()

    class Meta:
        database = db  # This model uses the 'game.db' database
        constraints = [p.SQL('UNIQUE ("name" COLLATE NOCASE)')]

class Planet(p.Model):
    star = p.ForeignKeyField(Star, backref='planets')
    numero = p.IntegerField()
    humidity = p.FloatField()
    temperature = p.FloatField()
    size = p.IntegerField()
    atmosphere = p.FloatField()

    def to_dict(self):
        return {
            "numero": self.numero,
            "humidity": self.humidity,
            "temperature": self.temperature,
        }

    class Meta:
        database = db  # This model uses the 'game.db' database
        indexes = (
            (("star", "numero"), True),  # unique index sur star and numero
        )

class Colony(p.Model):
    planet = p.ForeignKeyField(Planet, backref="colony")
    player = p.ForeignKeyField(Player, backref="colonies")
    name = p.CharField()
    WF = p.IntegerField(default=0)
    RO = p.IntegerField(default=0)
    food = p.IntegerField(default=0)
    parts = p.IntegerField(default=0)

    def to_dict(self):
        return {
            "colony_name": self.name,
            "WF": self.WF,
            "RO": self.RO,
            "food": self.food,
            "parts": self.parts
        }

    class Meta:
        database = db  # This model uses the 'game.db' database
        indexes = (
            (("planet", "player"), True),  # unique index sur star and numero
        )
        constraints = [p.SQL('UNIQUE ("name" COLLATE NOCASE)')]

def create_tables():
    db.create_tables([Player, Tech, Case, Star, Planet, Colony])

