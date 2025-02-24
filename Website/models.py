from enum import unique

from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(125), unique=True)
    email = db.Column(db.String(125), unique=True)
    password = db.Column(db.String(300))
    scoreValue = db.relationship('Scoreboard')

class Quiz(db.Model):
    __tablename__ = 'quiz'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question = db.Column(db.String(125), unique=True)
    optionOne = db.Column(db.String(125))
    optionTwo = db.Column(db.String(125))
    optionThree = db.Column(db.String(125))
    optionFour = db.Column(db.String(125))
    correctAns = db.Column(db.Integer)
    pointValue = db.Column(db.Integer)

class Scoreboard(db.Model):
    __tablename__ = 'scoreboard'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, db.ForeignKey('user.id'))
    userScore = db.Column(db.BigInteger)



