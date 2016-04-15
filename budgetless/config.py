from .db import DBPool, tbl_conf
from sqlalchemy.sql import func, select, update
import pickle as libpickle

class ConfigPool(DBPool):

    def all(self):
        return {}

    def has_key(self, key):
        with self.engine.begin() as conn:
            r = conn.execute(select([func.count()]).where(tbl_conf.c.option == key))
            if r.first()[0] > 0:
                return True
            return False

    def set(self, key, value, pickle=False):
        if pickle:
            value = libpickle.dumps(value)
        with self.engine.begin() as conn:
            r = conn.execute(select([func.count()]).where(tbl_conf.c.option == key))
            if r.first()[0] > 0:
                conn.execute(tbl_conf.update().where(tbl_conf.c.option == key).values(value=value, pickle=pickle))
            else:
                conn.execute(tbl_conf.insert().values(option=key, value=value, pickle=pickle))

    def get(self, key, value=None):
        with self.engine.begin() as conn:
            r = conn.execute(tbl_conf.select().where(tbl_conf.c.option == key))
            try:
                row = r.first()
                val = row.value
                if row.pickle is True:
                    val = libpickle.loads(val)
                return val
            except:
                return value

    def reset(self, key):
        with self.engine.begin() as conn:
            conn.execute(tbl_conf.delete().where(tbl_conf.c.option == key))
