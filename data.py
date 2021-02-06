import peewee as p

from names import generate_name

db = p.SqliteDatabase(None, autoconnect=True)

def use_db(path_to_db: str = "game", testing: bool = False):
    if testing:
        db.init(':memory:')
    else:
        db.init(f"{path_to_db}")

class Player(p.Model):
    name = p.CharField(unique=True)
    email = p.CharField()

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
    climat = p.FloatField()
    temperature = p.FloatField()
    size = p.IntegerField()
    atmosphere = p.FloatField()

    class Meta:
        database = db  # This model uses the 'game.db' database
        indexes = (
            (("star", "numero"), True),  # unique index sur star and numero
        )

def create_tables():
    db.create_tables([Player, Case, Star, Planet])

