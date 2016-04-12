from flask import Flask

from ..budget import Budget
from .blueprint import blueprint


def get_app_for_budget(budget):
    app = Flask(__name__)
    app.register_blueprint(blueprint)
    app.config['budget'] = budget or Budget()
    return app
