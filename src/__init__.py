from flask import Flask
from src.railml.controllers import railml
from src.vector.controllers import vector

app = Flask(__name__)

app.register_blueprint(railml)
app.register_blueprint(vector)
