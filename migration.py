import nightshades
from nightshades.models import User, LoginProvider, Unit, Tag

db = nightshades.connection()
db.execute_sql('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
db.create_tables([User, LoginProvider, Unit, Tag], safe = True)
