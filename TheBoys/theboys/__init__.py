from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

app = Flask(__name__)
app.config["SECRET_KEY"] = "superdupersecretkeythatnooneshouldknowabout"

DB_NAME1 = "Users"
DB_NAME2 = "ChatsSaved"
DB_NAME3 = "ActiveLobby"

app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{DB_NAME1}.sqlite3'
app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{DB_NAME2}.sqlite3'
app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{DB_NAME3}.sqlite3'

db = SQLAlchemy(app)
socketio = SocketIO(app)
app.app_context().push()

from theboys import routes