from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy() #This variable will be used to call upon SQLAlchemy() commands

#user table
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(200))
    meals = db.relationship('MealRecord', backref='user')
    exercises = db.relationship('ExerciseRecord', backref='user')
    #establishes link to the ExerciseRecord table, User.exercises would refer to both the exercises record and user databases
    #backref = 'user' allows ExerciseRecord.user to also be used, basically turning it into a two way link

#meal table
class MealRecord(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(200), nullable = False)
    time = db.Column(db.String(50), nullable = False)
    calories = db.Column(db.Integer, nullable = False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    #The ForeignKey is linked to the primary key of the User database

#exercise table
class ExerciseRecord(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    hours = db.Column(db.Integer, nullable = False)
    minutes = db.Column(db.Integer, nullable = False)
    intensity = db.Column(db.Integer, nullable = False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    #The ForeignKey is linked to the primary key of the User database
