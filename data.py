import peewee as p
from playhouse.kv import KeyValue

from names import generate_name

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
    name = p.CharField(unique=True)
    email = p.CharField()

    @property
    def tech(self):
        return self.techs.get()

    class Meta:
        database = db  # This model uses the 'game.db' database

class Tech(p.Model):
    player = p.ForeignKeyField(Player, backref="techs", unique=True)
    bio = p.IntegerField()
    meca = p.IntegerField()

    bio_points = p.IntegerField(default=0)
    meca_points = p.IntegerField(default=0)

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
    name = p.CharField(default=generate_name())

    class Meta:
        database = db  # This model uses the 'game.db' database

class Planet(p.Model):
    star = p.ForeignKeyField(Star, backref='planets')
    numero = p.IntegerField()
    humidity = p.FloatField()
    temperature = p.FloatField()
    size = p.IntegerField()
    atmosphere = p.FloatField()

    class Meta:
        database = db  # This model uses the 'game.db' database
        indexes = (
            (("star", "numero"), True),  # unique index sur star and numero
        )

class Colony(p.Model):
    planet = p.ForeignKeyField(Planet, backref="colony")
    owner = p.ForeignKeyField(Player, backref="colonies")
    WF = p.IntegerField(default=0)
    RO = p.IntegerField(default=0)

    class Meta:
        database = db  # This model uses the 'game.db' database
        indexes = (
            (("planet", "owner"), True),  # unique index sur star and numero
        )

def create_tables():
    db.create_tables([Player, Tech, Case, Star, Planet, Colony])

