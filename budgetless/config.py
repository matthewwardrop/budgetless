from .db import DBPool

class ConfigPool(DBPool):

    def all(self):
        return {}

    def set(self, key, value):
        pass

    def get(self, key, value=None):
        return value
