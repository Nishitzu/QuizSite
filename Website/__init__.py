from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

db = SQLAlchemy()
DB_NAME = "quizgame.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'WNQE?dmAUogdArC6QMrXiPIwBkBQfou5q2jOcYy=Xf6PPYUtpORH1bAbqJWfI5KDqAQ8iXkZhrHOyTJ8xe!hJUvXL8h1a4r/l81RHZo3//hi6XganwJZL9B!2PwTf5SU'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['API_KEY_WEATHER'] = 'N36qIAPidsamssadwYAG4YRmteA657Mx'
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    #Initializing model structure before database creation
    from .models import User, Quiz, Scoreboard

    create_database(app)

    #Login Manager segment
    loginManager = LoginManager()
    loginManager.login_view = 'auth.login' #default login view
    loginManager.init_app(app)
    #Define function to load user
    #In this case the get function references by primary key by default
    @loginManager.user_loader
    def userLoader(id):
        return User.query.get(int(id))

    return app

#Defining appropriate function to maintain cleaner structure
def create_database(app):
    #app object passed for context and database path
    with app.app_context():
        db.create_all()
        print('Created Database Successfully!')