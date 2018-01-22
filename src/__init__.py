from flask import Flask
from src.railml.controllers import railml

app = Flask(__name__)

app.register_blueprint(railml)

