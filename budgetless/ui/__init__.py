from flask import Flask

from ..budget import Budget
from .blueprint import blueprint


def get_app_for_budget(self, budget=None):
    app = Flask(__name__)
    app.register_blueprint(blueprint)
    app.config['budget'] = Budget() if budget is None else budget
    return app
