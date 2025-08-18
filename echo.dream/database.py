import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# create SQLAlchemy instance
db = SQLAlchemy(model_class=Base)

def init_app(app):
    """Initialize the database with the app."""
    # setup a secret key, required by sessions
    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"
    # configure the database, relative to the app instance folder
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    # initialize the app with the extension, flask-sqlalchemy >= 3.0.x
    db.init_app(app)